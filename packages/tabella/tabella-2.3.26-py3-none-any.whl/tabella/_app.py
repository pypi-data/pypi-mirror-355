"""Tabella class definitions."""

__all__ = ("Tabella",)

import asyncio
import datetime
import ssl
import sys
from pathlib import Path
from typing import Any, Callable, Type
from urllib import parse

import uvicorn
from jsonrpcobjects.objects import Notification, ParamsNotification, ParamsRequest
from jsonrpcobjects.objects import Request as RPCRequest
from openrpc import (
    APIKeyAuth,
    BearerAuth,
    Contact,
    License,
    OAuth2,
    RPCServer,
    SecurityFunction,
    Server,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, WebSocketRoute
from starlette.staticfiles import PathLike, StaticFiles
from uvicorn.config import (
    LOGGING_CONFIG,
    SSL_PROTOCOL_VERSION,
    HTTPProtocolType,
    InterfaceType,
    LifespanType,
    LoopSetupType,
    WSProtocolType,
)

from tabella import _monitor, _routes
from tabella._common import base_context, cache, root
from tabella._util import OAuthChallengeHandler

RequestType = ParamsRequest | RPCRequest | ParamsNotification | Notification


class Tabella(RPCServer):
    def __init__(  # noqa: PLR0913
        self,
        title: str | None = None,
        version: str | None = None,
        description: str | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_: License | None = None,
        servers: list[Server] | Server | None = None,
        security_schemes: dict[str, OAuth2 | BearerAuth | APIKeyAuth] | None = None,
        security_function: SecurityFunction | None = None,
        oauth_challenge_handler: OAuthChallengeHandler | None = None,
        client_gen_directory: Path | None = None,
        favicon_url: str | None = None,
        icon_url: str | None = None,
        *,
        debug: bool = False,
        disable_client_gen: bool = False,
        headless: bool = False,
    ) -> None:
        """App to register and host RPC methods.

        :param title: OpenRPC title.
        :param version: API version.
        :param description: Description of the app.
        :param terms_of_service: App terms of service.
        :param contact: Contact information.
        :param license_: App license.
        :param servers: Servers hosting this RPC API.
        :param security_schemes: Security schemes used by this RPC API.
        :param security_function: Function to get active security scheme
            of a method call. This function should accept middleware
            arguments as a parameter and can use `Depends` params.
        :param oauth_challenge_handler: Class to handle creating and getting
            OAuth verifiers from code challenges.
        :param client_gen_directory: Directory to write generated client
            files to.
        :param favicon_url: URL to favicon to use for docs site.
        :param icon_url: URL to icon to use in docs site.
        :param debug: Include internal error details in error responses.
        :param disable_client_gen: Disable client generation and download.
        :param headless: Run Tabella in headless mode.
        """
        super().__init__(
            title,
            version,
            description,
            terms_of_service,
            contact,
            license_,
            servers,
            security_schemes,
            security_function,
            debug=debug,
        )
        cache.debug = debug
        cache.disable_client_gen = disable_client_gen
        self.starlette = Starlette()

        # Setup default routes and app.
        routes: list[Route | WebSocketRoute] = [
            Route("/", _routes.index),
            Route("/docs/discover-{trigger}", _routes.discover),
            Route("/docs/try-it-modal/{method_idx}", _routes.try_it),
            Route(
                "/docs"
                "/add-{item_type}-item"
                "/{method_id}"
                "/{param_id}"
                "/{input_id}"
                "/{is_even}",
                _routes.add_item,
            ),
            Route("/openrpc.json", _routes.openrpc_doc),
            Route("/rpc-api", _routes.api_pass_through, methods=["POST"]),
            Route("/download-client/{version}", _routes.download_client),
        ]
        # Add monitoring routes if in debug.
        if debug:
            routes.append(Route("/monitor", _monitor.monitor))
            routes.append(WebSocketRoute("/monitor-ws", _monitor.monitor_ws))
        self.starlette.routes.extend(routes)
        self.starlette.mount(
            "/static", StaticFiles(directory=root / "static"), name="static"
        )

        # If no RPCServer provided, run in headless mode.
        if headless:
            return

        servers = self._get_servers()
        for server in servers:
            parsed_url = parse.urlparse(server.url)
            if parsed_url.scheme.startswith("http"):
                self.starlette.routes.append(
                    Route(parsed_url.path, self._get_http_function(), methods=["POST"])
                )
            elif parsed_url.scheme.startswith("ws"):
                self.starlette.routes.append(
                    WebSocketRoute(parsed_url.path, self._get_ws_function())
                )

        api_path = servers[0].url
        cache.set_request_processor(self.process_request_async, api_path)
        if client_gen_directory:
            cache.client_gen_directory = client_gen_directory
        if favicon_url:
            base_context["favicon_url"] = favicon_url
        if icon_url:
            base_context["icon_url"] = icon_url
        if oauth_challenge_handler:
            cache.oauth_handler = oauth_challenge_handler
        if len(servers) > 1:
            cache.servers = servers

    def run(  # noqa: PLR0913
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8000,
        uds: str | None = None,
        fd: int | None = None,
        loop: LoopSetupType = "auto",
        http: Type[asyncio.Protocol] | HTTPProtocolType = "auto",
        ws: Type[asyncio.Protocol] | WSProtocolType = "auto",
        ws_max_size: int = 16777216,
        ws_max_queue: int = 32,
        ws_ping_interval: float | None = 20.0,
        ws_ping_timeout: float | None = 20.0,
        ws_per_message_deflate: bool = True,
        lifespan: LifespanType = "auto",
        interface: InterfaceType = "auto",
        reload: bool = False,
        reload_dirs: list[str] | str | None = None,
        reload_includes: list[str] | str | None = None,
        reload_excludes: list[str] | str | None = None,
        reload_delay: float = 0.25,
        workers: int | None = None,
        env_file: str | PathLike | None = None,
        log_config: dict[str, Any] | str | None = None,
        log_level: str | int | None = None,
        access_log: bool = True,
        proxy_headers: bool = True,
        server_header: bool = True,
        date_header: bool = True,
        forwarded_allow_ips: list[str] | str | None = None,
        root_path: str = "",
        limit_concurrency: int | None = None,
        backlog: int = 2048,
        limit_max_requests: int | None = None,
        timeout_keep_alive: int = 5,
        timeout_graceful_shutdown: int | None = None,
        ssl_keyfile: str | None = None,
        ssl_certfile: str | PathLike | None = None,
        ssl_keyfile_password: str | None = None,
        ssl_version: int = SSL_PROTOCOL_VERSION,
        ssl_cert_reqs: int = ssl.CERT_NONE,
        ssl_ca_certs: str | None = None,
        ssl_ciphers: str = "TLSv1",
        headers: list[tuple[str, str]] | None = None,
        use_colors: bool | None = None,
        app_dir: str | None = None,
        factory: bool = False,
        h11_max_incomplete_event_size: int | None = None,
    ) -> None:
        """Run the application, wraps `uvicorn.run`."""
        log_config = log_config or LOGGING_CONFIG
        uvicorn.run(
            self.starlette,
            host=host,
            port=port,
            uds=uds,
            fd=fd,
            loop=loop,
            http=http,
            ws=ws,
            ws_max_size=ws_max_size,
            ws_max_queue=ws_max_queue,
            ws_ping_interval=ws_ping_interval,
            ws_ping_timeout=ws_ping_timeout,
            ws_per_message_deflate=ws_per_message_deflate,
            lifespan=lifespan,
            interface=interface,
            reload=reload,
            reload_dirs=reload_dirs,
            reload_includes=reload_includes,
            reload_excludes=reload_excludes,
            reload_delay=reload_delay,
            workers=workers,
            env_file=env_file,
            log_config=log_config,
            log_level=log_level,
            access_log=access_log,
            proxy_headers=proxy_headers,
            server_header=server_header,
            date_header=date_header,
            forwarded_allow_ips=forwarded_allow_ips,
            root_path=root_path,
            limit_concurrency=limit_concurrency,
            backlog=backlog,
            limit_max_requests=limit_max_requests,
            timeout_keep_alive=timeout_keep_alive,
            timeout_graceful_shutdown=timeout_graceful_shutdown,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            ssl_keyfile_password=ssl_keyfile_password,
            ssl_version=ssl_version,
            ssl_cert_reqs=ssl_cert_reqs,
            ssl_ca_certs=ssl_ca_certs,
            ssl_ciphers=ssl_ciphers,
            headers=headers,
            use_colors=use_colors,
            app_dir=app_dir,
            factory=factory,
            h11_max_incomplete_event_size=h11_max_incomplete_event_size,
        )

    @property
    def favicon_url(self) -> str | None:
        """URL to favicon to use for docs site."""
        return base_context.get("favicon_url")

    @favicon_url.setter
    def favicon_url(self, value: str | None) -> None:
        base_context["favicon_url"] = value

    @property
    def icon_url(self) -> str | None:
        """URL to icon to use in docs site."""
        return base_context.get("icon_url")

    @icon_url.setter
    def icon_url(self, value: str | None) -> None:
        base_context["icon_url"] = value

    @property
    def oauth_handler(self) -> OAuthChallengeHandler:
        """Disable client generation and download."""
        return cache.oauth_handler

    @oauth_handler.setter
    def oauth_handler(self, value: OAuthChallengeHandler) -> None:
        cache.oauth_handler = value

    @property
    def client_gen_directory(self) -> Path | None:
        """Directory to write generated client files to."""
        return cache.client_gen_directory

    @client_gen_directory.setter
    def client_gen_directory(self, value: Path | None) -> None:
        cache.client_gen_directory = value

    def _get_servers(self) -> list[Server]:
        servers: list[Server] = []
        if not isinstance(self.servers, Server):
            servers = self.servers
        else:
            parsed_url = parse.urlparse(self.servers.url)
            if not (not parsed_url.scheme and parsed_url.path == "localhost"):
                servers = [self.servers]
            else:
                port = "8000"
                for arg in sys.argv:
                    if arg == "--port":
                        port = sys.argv[sys.argv.index(arg) + 1]
                        break
                servers.append(
                    Server(name="HTTP API", url=f"http://localhost:{port}/api")
                )
                servers.append(
                    Server(name="WebSocket API", url=f"ws://localhost:{port}/api")
                )
        return servers

    def _get_ws_function(self) -> Callable[..., Any]:
        from starlette.websockets import WebSocket, WebSocketDisconnect

        async def ws_process_rpc(websocket: WebSocket) -> None:
            """Process RPC requests through websocket."""
            try:
                await websocket.accept()

                async def _process_rpc(request: str) -> None:
                    rpc_response = await self.process_request_async(
                        request, websocket.headers
                    )
                    if rpc_response is not None:
                        await websocket.send_text(rpc_response)

                while True:
                    data = await websocket.receive_text()
                    _ = asyncio.create_task(_process_rpc(data))
            except WebSocketDisconnect:
                pass

        async def ws_process_rpc_debug(websocket: WebSocket) -> None:
            """Process RPC requests through websocket in debug."""
            try:
                await websocket.accept()
                te = await cache.get_templating_engine()

                async def _process_rpc(request: str) -> None:
                    start = datetime.datetime.now()
                    rpc_response = await self.process_request_async(
                        request, websocket.headers
                    )
                    queue_msg = {
                        "caller_details": websocket.headers,
                        "duration": (datetime.datetime.now() - start).total_seconds(),
                        "request": request,
                        "response": rpc_response,
                    }
                    for q in te.queues:
                        await q.put(queue_msg)
                    if rpc_response is not None:
                        await websocket.send_text(rpc_response)

                while True:
                    data = await websocket.receive_text()
                    _ = asyncio.create_task(_process_rpc(data))
            except WebSocketDisconnect:
                pass

        return ws_process_rpc_debug if self.debug else ws_process_rpc

    def _get_http_function(self) -> Callable[..., Any]:
        async def http_process_rpc(request: Request) -> Response:
            """Process RPC request through HTTP server."""
            rpc_request = await request.body()
            rpc_response = await self.process_request_async(
                rpc_request, request.headers
            )
            return Response(content=rpc_response, media_type="application/json")

        async def http_process_rpc_debug(request: Request) -> Response:
            """Process RPC request through HTTP server in debug."""
            rpc_request = await request.body()
            start = datetime.datetime.now()
            rpc_response = await self.process_request_async(
                rpc_request, request.headers
            )
            queue_msg = {
                "caller_details": request.headers,
                "duration": (datetime.datetime.now() - start).total_seconds(),
                "request": rpc_request,
                "response": rpc_response,
            }
            te = await cache.get_templating_engine()
            for q in te.queues:
                await q.put(queue_msg)
            return Response(content=rpc_response, media_type="application/json")

        return http_process_rpc_debug if self.debug else http_process_rpc
