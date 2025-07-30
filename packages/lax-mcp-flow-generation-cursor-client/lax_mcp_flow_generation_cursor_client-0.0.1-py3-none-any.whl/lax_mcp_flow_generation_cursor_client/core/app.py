from fastmcp import FastMCP
from lax_mcp_flow_generation_cursor_client.utils.logger import get_logger
from lax_mcp_flow_generation_cursor_client.core.settings import settings
from lax_mcp_flow_generation_cursor_client.tools import PROXY_TOOLS
from lax_mcp_flow_generation_cursor_client.core.client import backend_client

logger = get_logger(__name__)

class MCPProxyComponents:
    """Helper class to manage MCP proxy components registration."""

    @staticmethod
    def register_components(mcp: FastMCP) -> None:
        """Register all proxy components with the MCP server."""
        # Register proxy tools
        for tool_name, tool_function in PROXY_TOOLS.items():
            try:
                mcp.tool(name=tool_name)(tool_function)
                logger.info(f"Registered proxy tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to register proxy tool {tool_name}: {e}")

# Create the proxy MCP server
mcp_server = FastMCP(
    name=settings.MCP_SERVER_NAME,
    instructions=settings.MCP_SERVER_DESCRIPTION,
)

# Register proxy components
MCPProxyComponents.register_components(mcp_server)

# Create the app for potential HTTP usage (not used for stdio)
app = mcp_server

if __name__ == "__main__":
    # Run with stdio transport for Cursor compatibility
    logger.info("Starting MCP proxy server with stdio transport...")
    mcp_server.run(transport="stdio") 