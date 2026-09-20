import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    params = StdioServerParameters(command="python", args=["mcp_tools.py"])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"Tools available: {[t.name for t in tools.tools]}")
            result = await session.call_tool("calculator", {"expression": "85000 * 0.15"})
            print(f"Calculator: {result.content[0].text}")
            result = await session.call_tool("date_utilities", {"operation": "today"})
            print(f"Date: {result.content[0].text}")

asyncio.run(test())