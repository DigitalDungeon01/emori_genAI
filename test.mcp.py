import os
import asyncio
from agents.mcp import MCPServerStdio

async def inspect_tavily_tools():
    env = {"TAVILY_API_KEY": "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"}
    params = {
        "command": "npx",
        "args": ["-y", "tavily-mcp@latest"],
        "env": env
    }
    
    async with MCPServerStdio(params=params) as server:
        tools = await server.list_tools()
        
        for tool in tools:
            print(f"\n🔧 Tool: {tool.name}")
            print(f"📝 Description: {tool.description}")
            print(f"⚙️ Parameters: {tool.inputSchema}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(inspect_tavily_tools())