import os
from typing import Optional

class Settings:
    """Settings for the cursor client MCP server."""
    
    # Server settings
    MCP_SERVER_NAME: str = "LAX Flow Generation MCP Server"
    MCP_SERVER_DESCRIPTION: str = "Flow Generation MCP Server which provides tools for generating and updating flows in LambdaX (LAX)"

    # Workspace
    WORKSPACE_PATH: Optional[str] = os.getenv("WORKSPACE_PATH", None)
    
    # Backend server settings
    BACKEND_SERVER_URL: str = os.getenv("BACKEND_SERVER_URL", "http://localhost:8000/mcp")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # File handling settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default

settings = Settings() 