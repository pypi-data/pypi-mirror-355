"""CLI entry point for the Cal.com MCP server."""

import typer
from .server import mcp

app = typer.Typer()


@app.command()
def stdio():
    """Run the Cal.com MCP server using stdio transport."""
    mcp.run(transport="stdio")


@app.command()
def sse(
    host: str = "localhost",
    port: int = 9557,
):
    """Run the Cal.com MCP server using SSE transport.
    
    Args:
        host: The host to bind to (default: localhost)
        port: The port to bind to (default: 9557)
    """
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="sse")


@app.command()
def streamable_http(
    host: str = "localhost",
    port: int = 9558,
):
    """Run the Cal.com MCP server using streamable HTTP transport.
    
    Args:
        host: The host to bind to (default: localhost)
        port: The port to bind to (default: 9558)
    """
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    app(["stdio"]) 