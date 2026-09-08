import asyncio

from fastmcp import Client

from common.config import MCP_GATEWAY_URL


async def main():

    print("=" * 60)
    print("MCP URL:")
    print(MCP_GATEWAY_URL)
    print("=" * 60)

    async with Client(MCP_GATEWAY_URL) as client:

        print("\nConnected to MCP server.")

        tools = await client.list_tools()

        print("\nAvailable MCP tools:")
        print("-" * 60)

        for tool in tools:
            print(tool.name)

        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
