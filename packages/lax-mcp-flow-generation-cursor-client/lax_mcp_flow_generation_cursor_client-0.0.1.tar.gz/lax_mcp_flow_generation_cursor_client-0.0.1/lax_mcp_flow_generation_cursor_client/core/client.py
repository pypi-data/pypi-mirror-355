import asyncio
from typing import Dict, Any, Optional
from fastmcp import Client
from lax_mcp_flow_generation_cursor_client.utils.logger import get_logger
from lax_mcp_flow_generation_cursor_client.core.settings import settings

logger = get_logger(__name__)

class BackendMCPClient:
    """Client wrapper for connecting to the backend MCP server."""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._backend_url = settings.BACKEND_SERVER_URL
        
    async def connect(self):
        """Connect to the backend MCP server."""
        if self._client is None:
            try:
                logger.info(f"Connecting to backend MCP server at {self._backend_url}")
                self._client = Client(self._backend_url)
                await self._client.__aenter__()
                logger.info("Successfully connected to backend MCP server")
            except Exception as e:
                logger.error(f"Failed to connect to backend MCP server: {e}")
                raise
                
    async def disconnect(self):
        """Disconnect from the backend MCP server."""
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
                self._client = None
                logger.info("Disconnected from backend MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from backend MCP server: {e}")
                
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Forward a tool call to the backend server."""
        if not self._client:
            await self.connect()
            
        try:
            logger.info(f"Forwarding tool call: {tool_name} with args: {arguments}")
            result = await self._client.call_tool(tool_name, arguments)
            logger.info(f"Tool call successful: {tool_name}")
            if len(result) == 1:
                result = result[0]
            
            # Convert the result to a dictionary format
            if hasattr(result, 'text'):
                return result.text
            elif hasattr(result, 'content'):
                return result.content
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
            
    async def list_tools(self):
        """List available tools from the backend server."""
        if not self._client:
            await self.connect()
            
        try:
            tools = await self._client.list_tools()
            return tools
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []

# Global client instance
backend_client = BackendMCPClient() 