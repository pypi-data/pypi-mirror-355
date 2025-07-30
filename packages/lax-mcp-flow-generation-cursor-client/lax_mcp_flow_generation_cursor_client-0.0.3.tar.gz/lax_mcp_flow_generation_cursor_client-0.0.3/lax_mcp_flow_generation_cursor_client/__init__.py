from lax_mcp_flow_generation_cursor_client.core.app import app

__version__ = "0.0.1"
__all__ = ["app"]

def main():
    app.run(transport="stdio")

if __name__ == "__main__":
    main()