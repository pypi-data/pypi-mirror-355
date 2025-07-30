"""Tabella web UI routes."""

import json
import shutil
from typing import Any

import caseswitcher
from openrpc import OAuth2, OpenRPC, Schema, SchemaType
from openrpcclientgenerator import generate, Language
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response

import tabella._util as util
from tabella._common import base_context, cache, httpx, root, templates
from tabella._templating_engine import TemplatingEngine


async def index(request: Request) -> Response:
    """Get interactive docs site."""
    scheme = None
    enabled_scopes = []
    client_id = None

    # If state is provided this is redirect from OAuth server.
    state = request.query_params.get("state")
    if not state:
        te = await cache.get_templating_engine()
    else:
        code = request.query_params.get("code")
        hash_, scheme, scopes, client_id, api_url = state.split("@")
        enabled_scopes = scopes.split(" ")
        if not (verifier := cache.oauth_handler.get_verifier(hash_)):
            return _error(request, "Server Error", "OAuth 2.0 verifier is missing.")

        te = await cache.get_templating_engine(api_url)
        # This shouldn't happen but needed for type safety.
        if te.rpc.components is None:
            return _error(
                request,
                "Server Error",
                "This server does not have an OAuth 2.0. security scheme",
            )

        schemes = te.rpc.components.x_security_schemes or {}
        for i, name in enumerate(schemes):
            if i != int(scheme):
                continue
            security_scheme = schemes[name]
            if not isinstance(security_scheme, OAuth2):
                continue
            token_url = security_scheme.flows[0].token_url
            client = httpx.AsyncClient()
            result = await client.post(
                f"{token_url}?code={code}&code_verifier={verifier}&grant_type=token"
            )
            te.headers = {"Authorization": f"Bearer {result.json()['access_token']}"}
            break

    context = {
        "request": request,
        "disable_api_input": cache.api_url is not None,
        "disable_client_gen": cache.disable_client_gen,
        "api_url": te.api_url,
        "te": te,
        "examples": util.get_examples(te.rpc.methods),
        "servers": cache.servers,
        "code_challenge": cache.oauth_handler.create_verifier(),
        "enabled_scheme": scheme,
        "enabled_scopes": enabled_scopes,
        "client_id": client_id,
        "debug": cache.debug,
    }
    return templates.TemplateResponse("index.html", {**context, **base_context})


async def discover(request: Request) -> Response:
    """Get OpenRPC docs."""
    api_url = request.query_params.get("api-url")
    trigger = request.path_params["trigger"]
    te = await cache.get_templating_engine(api_url, refresh=trigger == "click")

    context = {
        "disable_client_gen": cache.disable_client_gen,
        "request": request,
        "te": te,
        "examples": util.get_examples(te.rpc.methods),
        "code_challenge": cache.oauth_handler.create_verifier(),
    }
    return templates.TemplateResponse("openrpc_docs.html", {**context, **base_context})


async def try_it(request: Request) -> Response:
    """Get "Try it out" modal for a method."""
    api_url = request.query_params.get("api-url")
    method_idx = request.path_params["method_idx"]
    te = await cache.get_templating_engine(api_url)
    method = te.get_method(int(method_idx))
    context = {
        "request": request,
        "method": method,
        "method_id": method_idx,
        "get_any_default": util.get_any_default,
    }
    return templates.TemplateResponse("modals/try_it.html", {**context, **base_context})


async def add_item(request: Request) -> Response:
    """Get "Try it out" modal for a method."""
    api_url = request.query_params.get("api-url")
    item_count = request.query_params.get("item-count")
    method_id = request.path_params["method_id"]
    param_id = int(request.path_params["param_id"])
    input_id = request.path_params["input_id"]
    item_type = request.path_params["item_type"]
    is_even = int(request.path_params["is_even"])
    te = await cache.get_templating_engine(api_url)
    method = te.get_method(int(method_id))

    # Get schema for this param.
    param_schema: SchemaType = Schema()
    for i, param in enumerate(method.params):
        if i == param_id:
            param_schema = param.schema_
            break

    # We already got param schema from method, remove those ids.
    input_tree_path = input_id.removeprefix(f"{method_id}_{param_id}")
    # Get input ids to get proper schema in schema tree.
    input_ids = [id_.removeprefix("item") for id_ in input_tree_path.split("_") if id_]
    param_schema = util.get_schema_from_input_ids(param_schema, map(int, input_ids))

    if (
        item_type == "array"
        and not isinstance(param_schema, bool)
        and param_schema.items
    ):
        param_schema = param_schema.items
    if item_type != "recursive":
        input_id = f"{input_id}_item{item_count}"

    context = {
        "request": request,
        "method_id": method_id,
        "param_id": str(param_id),
        "schema": param_schema,
        "input_id": input_id,
        "minimalize": True,
        "required": True,
        "get_any_default": util.get_any_default,
        "is_even": 0 if is_even else 1,
    }
    if item_type == "object":
        return templates.TemplateResponse(
            "schema_form/object.html", {**context, **base_context}
        )
    return templates.TemplateResponse(
        "schema_form/form.html", {**context, **base_context}
    )


async def openrpc_doc(request: Request) -> JSONResponse:
    """Get raw OpenRPC JSON document."""
    api_url = request.query_params.get("api-url")
    te = await cache.get_templating_engine(api_url)
    return JSONResponse(content=await _discover(te))


async def api_pass_through(request: Request) -> Response:
    """Pass RPC requests to RPC server and get response."""
    api_url = request.query_params.get("api-url")
    te = await cache.get_templating_engine(api_url)

    # Set request headers based on security scheme.
    components = te.rpc.components
    scheme_is_set = False
    if components and components.x_security_schemes:
        for i, name in enumerate(components.x_security_schemes):
            if value := request.headers.get(f"scheme{i}"):
                scheme_is_set = True
                scheme = components.x_security_schemes[name]
                if scheme.type == "bearer":
                    te.headers = {scheme.name: f"Bearer {value}"}
                elif scheme.type == "apikey":
                    te.headers = {scheme.name: value}
                break
    # If no scheme is set clear any existing headers.
    if not scheme_is_set:
        te.headers = {}

    response = await te.process_request(await request.json())
    return Response(content=response, media_type="application/json")


async def download_client(request: Request) -> FileResponse:
    """Download a generated client for this API."""
    if cache.disable_client_gen:
        msg = "Client generation is disabled."
        raise ValueError(msg)
    # Get RPC data and target language.
    api_url = request.query_params["api-url"]
    language = request.query_params["language"]
    te = await cache.get_templating_engine(api_url)
    rpc = OpenRPC(**await _discover(te))
    lang_option = Language.PYTHON if language == "Python" else Language.TYPESCRIPT

    # Make generated out directories if they don't exist.
    out = cache.client_gen_directory or root.joinpath("static/out")
    out.mkdir(exist_ok=True)
    lang_out = out.joinpath(language.lower())
    lang_out.mkdir(exist_ok=True)
    transport = "http" if api_url.startswith("http") else "ws"
    client_name = caseswitcher.to_kebab(rpc.info.title) + f"-{transport}-client"
    client_dir = lang_out.joinpath(client_name)
    filename = f"{client_name}-{rpc.info.version}-{lang_option.value}.zip"
    zip_file = lang_out.joinpath(filename)

    # If client doesn't exist, generate and zip it.
    if not zip_file.exists():
        generate(rpc, lang_option, api_url, out)
        shutil.make_archive(zip_file.as_posix().removesuffix(".zip"), "zip", client_dir)

    # Serve the client zipfile.
    return FileResponse(zip_file, headers={"Content-Disposition": filename})


async def _discover(te: TemplatingEngine) -> dict[str, Any]:
    discover_request = {"id": 1, "method": "rpc.discover", "jsonrpc": "2.0"}
    response = await te.process_request(discover_request)
    return json.loads(response)["result"]


def _error(request: Request, error_title: str, error_message: str) -> Response:
    context = {
        "request": request,
        "error_title": error_title,
        "error_message": error_message,
    }
    return templates.TemplateResponse("error.html", context)
