"""Resources for the CVAD MCP Server."""

from mcp.server.fastmcp import FastMCP

from daas_mcp_server.constants import SENSITIVE_TOOLS_RESOURCE_PATH
from daas_mcp_server.tools import SENSITIVE_TOOLS

# Create an MCP server
mcp = FastMCP("daas_mcp_server")


@mcp.resource(SENSITIVE_TOOLS_RESOURCE_PATH, mime_type="application/json")
async def list_sensitive_tools() -> list[str]:
    """List all sensitive tools."""
    return [tool.__name__ for tool in SENSITIVE_TOOLS]
