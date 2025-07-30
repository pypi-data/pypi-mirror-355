import argparse
from fastmcp import FastMCP
from hkopenai.hk_education_mcp_server import tool_primary_schools_enrolment
from typing import Dict, List, Annotated, Optional
from pydantic import Field

def create_mcp_server():
    """Create and configure the MCP server"""
    mcp = FastMCP(name="HK OpenAI education Server")

    @mcp.tool(
        description="Student enrolment in primary schools by district and grade in Hong Kong from Education Bureau"
    )
    def get_student_enrolment_by_district() -> List[Dict]:
        return tool_primary_schools_enrolment.get_student_enrolment_by_district()

    return mcp
def main():
    parser = argparse.ArgumentParser(description='HKO MCP Server')
    parser.add_argument('-s', '--sse', action='store_true',
                       help='Run in SSE mode instead of stdio')
    args = parser.parse_args()

    server = create_mcp_server()
    
    if args.sse:
        server.run(transport="streamable-http")
        print("HKO MCP Server running in SSE mode on port 8000")
    else:
        server.run()
        print("HKO MCP Server running in stdio mode")

if __name__ == "__main__":
    main()
