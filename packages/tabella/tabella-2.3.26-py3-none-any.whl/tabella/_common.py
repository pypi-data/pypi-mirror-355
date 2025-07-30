"""Shared components."""

import importlib
from pathlib import Path
from typing import Any

from openrpc import ParamStructure, Schema
from starlette.templating import Jinja2Templates

from tabella import _util as util
from tabella._cache import TabellaCache

try:
    httpx = importlib.import_module("httpx")
except ImportError:
    httpx = None  # type: ignore

root = Path(__file__).parent
cache = TabellaCache.get_instance()

base_context: dict[str, Any] = {
    "len": len,
    "str": str,
    "id": lambda x: f"_{x}",
    "array_item_id": lambda x: f"_item{x}",
    "is_any": util.is_any,
    "is_str": lambda x: isinstance(x, str),
    "is_": lambda x, y: x is y,
    "ParamStructure": ParamStructure,
    "key_schema": Schema(type="string"),
    "httpx_missing": httpx is None,
}

templates = Jinja2Templates(
    directory=(root / "templates").as_posix(), lstrip_blocks=True, trim_blocks=True
)
