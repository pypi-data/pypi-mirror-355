import argparse
from fastmcp import FastMCP
from hkopenai.hk_law_mcp_server import foreign_domestic_helpers
from typing import Dict, List, Annotated, Optional, Union
from pydantic import Field

def create_mcp_server():
    """Create and configure the MCP server"""
    mcp = FastMCP(name="HK OpenAI Law and Security Server")

    @mcp.tool(
        description="Statistics on Foreign Domestic Helpers in Hong Kong. Data source: Immigration Department"
    )
    def get_fdh_statistics(
        year: Annotated[Optional[int], Field(description="Filter by specific year")] = None
    ) -> Dict[str, Union[Dict[str, str], List[Dict[str, str]], str]]:
        return foreign_domestic_helpers.get_fdh_statistics(year)

    return mcp
def main():
    parser = argparse.ArgumentParser(description='HK OpenAI Law and Security Server"')
    parser.add_argument('-s', '--sse', action='store_true',
                       help='Run in SSE mode instead of stdio')
    args = parser.parse_args()

    server = create_mcp_server()
    
    if args.sse:
        server.run(transport="streamable-http")
        print("Server running in SSE mode on port 8000")
    else:
        server.run()
        print("Server running in stdio mode")

if __name__ == "__main__":
    main()
