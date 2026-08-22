"""/mcp_server — one process, two surfaces over the same business logic.

  • MCP (for Claude)      → /mcp   (stdio locally; Streamable HTTP when deployed)
  • REST API (for humans) → /api   (FastAPI; only served in HTTP/deploy mode)

All knobs live in ONE file: config.py.

Local (stdio, MCP only):   poetry run python mcp_server/server.py
Connect Claude:            claude mcp add erkang -- poetry -C "$(pwd)" run python "$(pwd)/mcp_server/server.py"
Deployed (HTTP, both):     platforms inject PORT → serves /mcp AND /api. Connect Claude with
                           claude mcp add --transport http erkang https://<your-app>/mcp

(The folder is named mcp_server, NOT mcp, on purpose: a local `mcp/` package
would collide with the installed `mcp` SDK and break imports.)
"""
import sys
from pathlib import Path

# Make your project modules and config.py importable no matter where the server is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

import config
from api.server import run, say_hi, calculate

# --- MCP surface (tools) -------------------------------------------------
mcp = FastMCP(config.AGENT_NAME, host=config.HOST, port=config.PORT)


@mcp.tool()
def tool_say_hi() -> str:
    """Say hi, prefixed with this MCP server's timezone and current time."""
    return say_hi()


@mcp.tool()
def tool_run(payload: str = "ping") -> str:
    """Placeholder tool; delegates to your business logic in /api."""
    return run(payload)


@mcp.tool()
def tool_calculate(expression: str = "2 + 2") -> str:
    """Evaluate a math expression (supports +, -, *, /, **)."""
    return calculate(expression)


# --- combined ASGI app: MCP at /mcp + REST at /api (HTTP/deploy mode) -----
def build_http_app():
    """FastAPI app serving the REST API, with the MCP server mounted at /mcp.

    The MCP session manager must run inside the app lifespan — a mounted
    sub-app's own lifespan is NOT started by the parent, so we start it here.
    """
    from contextlib import asynccontextmanager

    from fastapi import FastAPI

    mcp_app = mcp.streamable_http_app()  # Starlette app that serves /mcp

    @asynccontextmanager
    async def lifespan(_app):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title=f"{config.AGENT_NAME} API", lifespan=lifespan)

    # Your REST endpoints — add more as you grow /api. Same logic the tools use.
    @app.get("/api/say_hi")
    def api_say_hi():
        return {"message": say_hi()}

    @app.get("/api/run")
    def api_run(payload: str = "ping"):
        return {"result": run(payload)}

    @app.get("/api/health")
    def api_health():
        return {"ok": True, "agent": config.AGENT_NAME}

    app.mount("/", mcp_app)  # /mcp is served by the mounted MCP app
    return app


if __name__ == "__main__":
    if config.MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")          # local: Claude over stdin/stdout (no HTTP, no /api)
    else:
        import uvicorn

        uvicorn.run(build_http_app(), host=config.HOST, port=config.PORT)  # deployed: /mcp + /api
