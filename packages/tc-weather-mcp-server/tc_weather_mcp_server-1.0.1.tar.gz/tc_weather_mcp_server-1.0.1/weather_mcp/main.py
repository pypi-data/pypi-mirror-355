"""Entry point for Weather MCP Server"""

def main():
    """Main entry point for the weather MCP server"""
    from .server import mcp
    print("Starting Weather MCP Server...")
    mcp.run()

if __name__ == "__main__":
    main()