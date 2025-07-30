import anyio
import typer

from daydream import mcp
from daydream.cli._app import app
from daydream.cli.options import PROFILE_OPTION
from daydream.telemetry import client as telemetry


@app.command()
def start(
    profile: str = PROFILE_OPTION,
    disable_sse: bool = typer.Option(
        False, "--disable-sse", help="Disable the SSE transport for the MCP Server"
    ),
    disable_stdio: bool = typer.Option(
        False, "--disable-stdio", help="Disable the stdio transport for the MCP Server"
    ),
) -> None:
    """Start the Daydream MCP Server"""

    async def _start() -> None:
        await telemetry.send_event(
            {
                "command": "start",
                "profile": profile,
                "disable_sse": disable_sse,
                "disable_stdio": disable_stdio,
            }
        )
        await mcp.start(profile, disable_sse, disable_stdio)

    anyio.run(_start)
