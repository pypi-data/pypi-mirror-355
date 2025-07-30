import json
import os
from typing import Dict, Any, Union
from pathlib import Path
from lax_mcp_flow_generation_cursor_client.utils.logger import get_logger
from lax_mcp_flow_generation_cursor_client.core.settings import settings

logger = get_logger(__name__)

class FileHandler:
    """Utility class for handling file operations."""
    
    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read a JSON file and return its contents."""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                # Try getting current working directory
                current_dir = Path.cwd()
                if (current_dir / file_path).exists():
                    file_path = current_dir / file_path
                else:
                    # Try from workspace path
                    if settings.WORKSPACE_PATH:
                        workspace_path = Path(settings.WORKSPACE_PATH)
                        if (workspace_path / file_path).exists():
                            file_path = workspace_path / file_path
                        else:
                            raise FileNotFoundError(f"File not found: {file_path} | Ensure you are using the entire full absolute path to the file not just the relative path")
                    else:
                        raise FileNotFoundError(f"File not found: {file_path} | Ensure you are using the entire full absolute path to the file not just the relative path")

            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > settings.MAX_FILE_SIZE:
                raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)")
            
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            logger.info(f"Successfully read JSON file: {file_path}")
            return content
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: Dict[str, Any]) -> None:
        """Write data to a JSON file."""
        try:
            file_path = Path(file_path)
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully wrote JSON file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise
    
    @staticmethod
    def read_text_file(file_path: Union[str, Path]) -> str:
        """Read a text file and return its contents."""
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > settings.MAX_FILE_SIZE:
                raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)")
            
            # Read text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Successfully read text file: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    @staticmethod
    def is_valid_path(file_path: Union[str, Path]) -> bool:
        """Check if a file path is valid and accessible."""
        try:
            file_path = Path(file_path)
            return file_path.exists() and file_path.is_file()
        except Exception:
            return False

# Global file handler instance
file_handler = FileHandler() 