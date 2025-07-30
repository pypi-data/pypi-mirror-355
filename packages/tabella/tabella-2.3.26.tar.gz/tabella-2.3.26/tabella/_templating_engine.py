"""Used to handle templating variables and string sanitization."""

import asyncio
import datetime
import importlib
import inspect
import json
from copy import copy
from typing import Any

from jinja2 import Undefined
from openrpc import Contact, Method, OAuth2, OpenRPC, RPCServer, SchemaType, Tag

from tabella._util import RequestProcessor

try:
    websockets = importlib.import_module("websockets")
except ImportError:
    websockets = None  # type: ignore
try:
    httpx = importlib.import_module("httpx")
except ImportError:
    httpx = None  # type: ignore

_rpc_server = RPCServer(
    title="Tabella",
    version="1.0.0",
    description="OpenRPC Interactive API Documentation",
    contact=Contact(
        name="Tabella Source Code",
        url="https://gitlab.com/mburkard/tabella",
    ),
)


class TemplatingEngine:
    """Get templating variables."""

    def __init__(
        self,
        api_url: str | None,
        request_processor: RequestProcessor | None = None,
        *,
        debug: bool = False,
    ) -> None:
        self.tags: list[Tag] = []
        self.api_url = api_url
        self.request_processor = request_processor
        self.rpc = OpenRPC(**_rpc_server.discover())
        self.headers: dict[str, str] = {}
        self.queues: list[asyncio.Queue[Any]] = []
        self.debug: bool = debug

    async def init(self) -> None:
        """Init a Templating Engine."""
        if self.api_url is None:
            self.rpc = await self._get_rpc(OpenRPC(**_rpc_server.discover()))
        else:
            self.rpc = await self._get_rpc()
        # Get all tags used in methods.
        for method in self.rpc.methods:
            for tag in method.tags or []:
                if tag not in self.tags:
                    self.tags.append(tag)

    def get_tags(self, method: Method) -> list[int]:
        """Gat indexes of tags for the given method."""
        return [
            i for i, tag in enumerate(self.tags or []) if tag in (method.tags or [])
        ]

    def get_method(self, idx: int) -> Method:
        """Get method with the given index."""
        for i, method in enumerate(self.rpc.methods):
            if i == idx:
                return method
        msg = f"No method at index {idx}."
        raise ValueError(msg)

    async def _get_rpc(self, rpc_doc: OpenRPC | None = None) -> OpenRPC:
        if not rpc_doc:
            discover = {"id": 1, "method": "rpc.discover", "jsonrpc": "2.0"}
            resp = json.loads(await self.process_request(discover))
            try:
                rpc_doc = OpenRPC(**resp["result"])
            except KeyError as e:
                msg = resp["error"]
                raise ValueError(msg) from e
        if rpc_doc.components is None or rpc_doc.components.schemas is None:
            return rpc_doc

        # Resolve references in schemas and filter methods by server.
        methods: list[Method] = []
        for method in rpc_doc.methods:
            if method.servers and self.api_url not in [s.url for s in method.servers]:
                continue
            for param in method.params:
                param.schema_ = resolve_references(
                    param.schema_, rpc_doc.components.schemas
                )
            method.result.schema_ = resolve_references(
                method.result.schema_, rpc_doc.components.schemas
            )
            methods.append(method)
        rpc_doc.methods = methods
        return rpc_doc

    async def process_request(self, request: dict[str, Any]) -> str:
        """Send a request to the RPC API and get a response."""
        queue_msg: dict[str, Any] = {}

        # Get method from methodId.
        if self.rpc:
            for i, m in enumerate(self.rpc.methods):
                if str(i) == request["method"]:
                    request["method"] = m.name
                    break

        rpc_request = json.dumps(request)

        # Custom Request Processor.
        if self.request_processor is not None:
            if self.debug:
                queue_msg["request"] = rpc_request
                start = datetime.datetime.now()
                resp = self.request_processor(rpc_request, self.headers)
                response = await resp if inspect.isawaitable(resp) else resp
                queue_msg["response"] = response
                queue_msg["duration"] = (
                    datetime.datetime.now() - start
                ).total_seconds()
                queue_msg["caller_details"] = self.headers
                for q in self.queues:
                    await q.put(queue_msg)
                return response or ""
            resp = self.request_processor(rpc_request, self.headers)
            return (await resp if inspect.isawaitable(resp) else resp) or ""

        # HTTP
        headers = {**{"Content-Type": "application/json"}, **self.headers}
        if self.api_url and self.api_url.startswith("http"):
            if httpx is None:
                msg = "httpx must be installed for HTTP APIs."
                raise ImportError(msg)
            client = httpx.AsyncClient()
            return (
                await client.post(
                    self.api_url,
                    content=rpc_request,
                    headers=headers,
                )
            ).content.decode()

        # Websocket
        if self.api_url and self.api_url.startswith("ws"):
            if websockets is None:
                msg = "websockets must be installed for WebSocket APIs."
                raise ImportError(msg)
            # Type ignore because `websockets` typing is wrong.
            async with websockets.connect(  # type: ignore
                self.api_url, extra_headers=headers
            ) as websocket:
                await websocket.send(rpc_request)
                return await websocket.recv()
        msg = "Invalid API URL."
        raise ValueError(msg)

    def get_security_id(self, security: dict[str, Any]) -> str:
        """Get ID to use for a security icon."""
        if (
            self.rpc.components is None
            or self.rpc.components.x_security_schemes is None
        ):
            return ""
        id_ = ""
        # Find matching scheme name.
        for s_name in security:
            for i, name in enumerate(self.rpc.components.x_security_schemes):
                if name != s_name:
                    continue
                id_ += f"scheme_{i}"
                scheme = self.rpc.components.x_security_schemes[name]
                # Find scope indexes.
                if not isinstance(scheme, OAuth2):
                    continue
                for j, scope in enumerate(scheme.flows[0].scopes):
                    for s_scope in security[name]:
                        if scope == s_scope:
                            id_ += f"_{j}"
        return id_

    def is_locked(
        self, method_id: str, enabled_scheme: str | Undefined, enabled_scopes: list[str]
    ) -> bool:
        """Determine if security method is locked."""
        if (
            self.rpc.components is None
            or self.rpc.components.x_security_schemes is None
            or enabled_scheme == Undefined
        ):
            return True

        method = self.get_method(int(method_id))
        if not method.x_security:
            return True
        for i, name in enumerate(self.rpc.components.x_security_schemes):
            if str(i) == enabled_scheme:
                if not (required_scopes := method.x_security.get(name)):
                    return True
                return not all(scope in enabled_scopes for scope in required_scopes)

        return True


def resolve_references(
    schema: SchemaType,
    schemas: dict[str, SchemaType],
    recurring: list[SchemaType] | None = None,
) -> SchemaType:
    """Resolve JSON Schema references."""
    if isinstance(schema, bool):
        return schema

    # Don't mutate original schema, will cause infinite recursion on
    # subsequent `resolve_references` calls with the same root schema.
    schema = copy(schema)

    # Don't mutate original recursion list, if mutated sibling schemas
    # will show as recursive for all but the first one.
    recurring = copy(recurring) if recurring else []

    if schema.ref:
        ref = schema.ref.removeprefix("#/components/schemas/")
        resolved_ref = copy(schemas[ref])
        if isinstance(resolved_ref, bool):
            return resolved_ref
        if schema in recurring:
            # Set `ref` to indicate recursion.
            resolved_ref.ref = schema.ref
            return resolved_ref
        resolved_ref.ref = None
        recurring.append(schema)
        schema = resolved_ref

    # Lists of schemas.
    for attr in ["all_of", "any_of", "one_of", "prefix_items"]:
        resolved: list[SchemaType] = []
        for child_schema in getattr(schema, attr) or []:  # type: ignore
            resolved_option = resolve_references(
                child_schema,  # type: ignore
                schemas,
                recurring,
            )
            resolved.append(resolved_option)
        if resolved:
            setattr(schema, attr, resolved)

    # Single schemas.
    for attr in [
        "not_",
        "property_names",
        "items",
        "contains",
        "if_",
        "then",
        "else_",
        "additional_properties",
    ]:
        if getattr(schema, attr):
            setattr(
                schema,
                attr,
                resolve_references(getattr(schema, attr), schemas, recurring),
            )

    # Dict of schemas.
    for attr in ["properties", "pattern_properties", "defs", "dependent_schemas"]:
        resolved_dict = {}
        for name, child_schema in (getattr(schema, attr) or {}).items():  # type: ignore
            resolved_dict[name] = resolve_references(
                child_schema,  # type: ignore
                schemas,
                recurring,
            )
        if resolved_dict:
            setattr(schema, attr, resolved_dict)

    return schema
