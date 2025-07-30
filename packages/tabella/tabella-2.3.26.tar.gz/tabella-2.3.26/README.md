# Tabella

![](https://img.shields.io/badge/License-ApacheV2-blue.svg)
![](https://img.shields.io/badge/code%20style-black-000000.svg)
![](https://img.shields.io/pypi/v/tabella.svg)

## Open-RPC development framework with builtin interactive documentation.

![Demo](https://gitlab.com/mburkard/tabella/-/raw/main/docs/demo.png)

## Live Demo

A live demo is available [here](https://tabella.burkard.cloud/).

## Install

Tabella is on PyPI and can be installed with:

```shell
pip install tabella
```

Or with [Poetry](https://python-poetry.org/)

```shell
poetry add tabella
```

## Python OpenRPC Docs

The RPC server hosted and documented by Tabella is powered
by [Python OpenRPC](https://gitlab.com/mburkard/openrpc). Refer to the Python OpenRPC
docs hosted [here](https://python-openrpc.burkard.cloud/) for advanced use.

## Getting Started

A basic Tabella app:

```python
from tabella import Tabella

app = Tabella()


@app.method()
def echo(a: str, b: float) -> tuple[str, float]:
    """Echo parameters back in result."""
    return a, b


if __name__ == "__main__":
    app.run()
```

Run this, then open http://127.0.0.1:8000/ in your browser to use the interactive
documentation.

The Open-RPC API will be hosted over HTTP on `http://127.0.0.1:8000/api` and over
WebSockets on `ws://127.0.0.1:8000/api`.

## Further Usage

### Routers

An app with many modules can be organized into segments
using [Method Routers](https://python-openrpc.burkard.cloud/method_routers).

### Security and Depends Arguments

Tabella passes request headers to the RPCServer process request methods. Details on
usage can be found in the Python OpenRPC docs on
[Depends Arguments](https://python-openrpc.burkard.cloud/security).

### Set Servers

Set RPC servers manually to specify transport and paths to host the RPC server on, e.g.

```python
from openrpc import Server
from tabella import Tabella

app = Tabella(
    servers=[
        Server(name="HTTP API", url="http://localhost:8000/my/api/path"),
        Server(name="WebSocket API", url="ws://localhost:8000/my/api/path"),
    ]
)
```

This app will host the RPCServer over HTTP and over WebSockets with the
path `/my/api/path`.

### Pydantic

[Pydantic](https://docs.pydantic.dev/latest/) is used for request/response
deserialization/serialization as well as schema generation. Pydantic should be used for
any models as seen here in
the [Python OpenRPC Docs](https://python-openrpc.burkard.cloud/basics#pydantic-for-data-models).

### Starlette

Tabella HTTP and WebSocket server hosting uses [Starlette](https://www.starlette.io/).
[Uvicorn](https://www.uvicorn.org/) can be used to run the starlette app.

```shell
uvicorn main:app.starlette --reload
```

## Monitor

If you are running the app with in debug mode, e.g. `app = Tabella(debug=True)`, then at
the path `/monitor` there is a display that will show requests and responses made to the
RPC server as they happen.

This requires `websockets`

```shell
pip install websockets
```

![Monitor](https://gitlab.com/mburkard/tabella/-/raw/main/docs/monitor_demo.png)

## Inspired By

- [OPEN-RPC Playground](https://playground.open-rpc.org/)
- [Swagger](https://swagger.io/)
- [Redoc](https://github.com/Redocly/redoc)

## Support The Developer

<a href="https://www.buymeacoffee.com/mburkard" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png"
       width="217"
       height="60"
       alt="Buy Me A Coffee">
</a>
