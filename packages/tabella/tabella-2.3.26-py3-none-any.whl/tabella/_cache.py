"""Provides RPCInterface to communicate with RPC server."""

import os
from pathlib import Path
from typing import Optional

from openrpc import Server

from tabella._templating_engine import TemplatingEngine
from tabella._util import DefaultHandler, OAuthChallengeHandler, RequestProcessor


class TabellaCache:
    """Handle communication with RPC server."""

    _instance: Optional["TabellaCache"] = None

    def __init__(self) -> None:
        if TabellaCache._instance:
            msg = "Do not instantiate RPCInterface directly, call `get_instance()`"
            raise ValueError(msg)
        self.api_url: str | None = os.environ.get("API_URL")
        self.cache: dict[str | None, TemplatingEngine] = {}
        self.request_processor: RequestProcessor | None = None
        self.servers: list[Server] = []
        self.oauth_handler: OAuthChallengeHandler = DefaultHandler()
        self.client_gen_directory: Path | None = None
        self.disable_client_gen: bool = False
        self.debug: bool = False

    @staticmethod
    def get_instance() -> "TabellaCache":
        """Get or create instance of RPCInterface."""
        if TabellaCache._instance:
            return TabellaCache._instance
        TabellaCache._instance = TabellaCache()
        return TabellaCache._instance

    def set_request_processor(
        self, request_processor: RequestProcessor, url: str
    ) -> None:
        """Set RPCServer to use for discovery and request processing."""
        self.request_processor = request_processor
        self.api_url = url

    async def get_templating_engine(
        self, api_url: str | None = None, *, refresh: bool = False
    ) -> TemplatingEngine:
        """Get a templating engine for the given API URL."""
        api_url = api_url or self.api_url
        if (te := self.cache.get(api_url)) and not refresh:
            return te
        if self.api_url and self.request_processor and not refresh:
            self.cache[api_url] = TemplatingEngine(
                self.api_url, self.request_processor, debug=self.debug
            )
        elif api_url is None:
            self.cache[api_url] = TemplatingEngine(None, debug=self.debug)
        else:
            self.cache[api_url] = TemplatingEngine(
                api_url, self.request_processor, debug=self.debug
            )
        await self.cache[api_url].init()
        return self.cache[api_url]
