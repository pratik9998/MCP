from typing import Any
import httpx 
from mcp.server.fastmcp import FastMCP
import asyncio

mcp = FastMCP("mcp-server")

# constants
HEALTHCHECK_URL = "http://localhost:6000/api/v1/healthcheck"
USER_AGENT = "MCP-Server/1.0"

# which actually makes the request
async def make_healthcheck_request(url: str) -> dict[str, Any] | None:
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

# mcp tools here    
@mcp.tool()
async def get_healthcheck() -> dict[str, Any]:
    """Get the health status of the web server.
    
    Returns:
        dict: A dictionary containing the health status of the web server.
        On success: {"status": "ok", "message": "server is running fine!!"}
        On failure: {"error": "Failed to get healthcheck"}
    """
    response = await make_healthcheck_request(HEALTHCHECK_URL)
    if response is None:
        return {"error": "Failed to get healthcheck"}
    return response

# main
if __name__ == "__main__":
    print("Starting MCP server...")
    print("Server name:", mcp.name)
    # Run the MCP server to make it available to client (like cursor ai or claude desktop)
    # mcp.run(transport='stdio')
    print(asyncio.run(get_healthcheck()))

