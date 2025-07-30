"""Monitor related endpoints and functions."""

import asyncio
import datetime
import importlib
import json
import signal
import sys
from typing import Any

from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request
from starlette.responses import Response

from tabella._common import base_context, cache, root, templates
import contextlib

try:
    websockets = importlib.import_module("websockets")
    starlette_websockets = importlib.import_module("starlette.websockets")
except ImportError:
    websockets = None  # type: ignore
    starlette_websockets = None  # type: ignore

env = Environment(
    loader=FileSystemLoader(root / "templates"),
    lstrip_blocks=True,
    trim_blocks=True,
    autoescape=True,
)
queues: list[asyncio.Queue[dict[str, Any] | bool]] = []
EXPAND_METHOD_AT = 100


async def monitor(request: Request) -> Response:
    """Get method call monitoring page."""
    te = await cache.get_templating_engine()
    context = {
        "api_url": te.api_url,
        "disable_api_input": cache.api_url is not None,
        "request": request,
        "servers": cache.servers,
        "te": te,
    }
    return templates.TemplateResponse("monitor/index.html", {**context, **base_context})


# `Any` since websocket may not be imported.
async def monitor_ws(websocket: Any) -> None:
    """Websocket for real-time method call monitoring."""
    if not queues:
        loop = asyncio.get_running_loop()

        def _shutdown(*_args: Any) -> None:
            loop.remove_signal_handler(signal.SIGINT)
            for q in queues:
                q.put_nowait(item=False)
            sys.exit()

        loop.add_signal_handler(signal.SIGINT, _shutdown)

    count = 0
    template_engine = await cache.get_templating_engine()
    queue: asyncio.Queue[dict[str, Any] | bool] = asyncio.Queue()
    template_engine.queues.append(queue)
    queues.append(queue)

    await websocket.accept()
    try:
        data: dict[str, Any]
        while data := await queue.get():  # type: ignore
            request = json.loads(data["request"])
            context = {
                "by_position": isinstance(request["params"], list),
                "caller_details": data["caller_details"],
                "count": count,
                "duration": data["duration"],
                "expand_params": len(data["request"]) > EXPAND_METHOD_AT,
                "request": request,
                "response": json.loads(data["response"]),
                "timestamp": datetime.datetime.now(),
            }
            with contextlib.suppress(
                websockets.ConnectionClosedOK,  # type: ignore
                starlette_websockets.WebSocketDisconnect,  # type: ignore
            ):
                await websocket.send_text(
                    env.get_template("monitor/method_call.html").render(context)
                )
            count += 1
    except (asyncio.exceptions.CancelledError, RuntimeError):
        pass


def _get_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, dict):
        return "object"
    return "array"


def _value_length(value: Any) -> int:
    return len(str(value))


env.globals.update(
    get_type=_get_type,  # type: ignore
    value_length=_value_length,  # type: ignore
    str=str,  # type: ignore
)
