"""DaaS MCP Server."""

from mcp.server.fastmcp import FastMCP

from daas_mcp_server.constants import (
    SENSITIVE_TOOLS_RESOURCE_PATH,
)
from daas_mcp_server.resources import list_sensitive_tools
from daas_mcp_server.tools import (
    check_ddc_power_state,
    get_latest_log,
    get_delivery_groups,
    get_machine_catalogs,
    restart_vda_machine,
)
from daas_mcp_server.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)
configure_logging()

# Create an MCP server
mcp = FastMCP("daas_mcp_server")

# Register resources
mcp.resource(SENSITIVE_TOOLS_RESOURCE_PATH, mime_type="application/json")(
    list_sensitive_tools
)

# Register tools
mcp.tool()(check_ddc_power_state)
mcp.tool()(get_latest_log)
mcp.tool()(get_delivery_groups)
mcp.tool()(get_machine_catalogs)
mcp.tool()(restart_vda_machine)


def main():
    """Run the MCP server."""
    logger.info("Starting the DaaS MCP Server")
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
