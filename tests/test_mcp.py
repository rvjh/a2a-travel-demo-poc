import asyncio

from fastmcp import Client


MCP_URL = "http://127.0.0.1:9000/mcp"


async def main():

    print("=" * 60)
    print("MCP TEST")
    print("=" * 60)

    print(f"\nConnecting to: {MCP_URL}")

    async with Client(MCP_URL) as client:

        print("Connected successfully!")

        # ----------------------------------------------------
        # LIST TOOLS
        # ----------------------------------------------------

        print("\nAvailable MCP tools:")

        tools = await client.list_tools()

        for tool in tools:
            print(f"  - {tool.name}")

        # ----------------------------------------------------
        # TEST FLIGHT SEARCH
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("Testing search_flights")
        print("=" * 60)

        flight_result = await client.call_tool(
            "search_flights",
            {
                "destination": "Goa",
            },
        )

        print("\nFlight result:")
        print(flight_result)

        # ----------------------------------------------------
        # TEST FLIGHT PRICE
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("Testing flight_price")
        print("=" * 60)

        price_result = await client.call_tool(
            "flight_price",
            {
                "destination": "Goa",
            },
        )

        print("\nCheapest flight price:")
        print(price_result)

        # ----------------------------------------------------
        # TEST HOTEL SEARCH
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("Testing search_hotels")
        print("=" * 60)

        hotel_result = await client.call_tool(
            "search_hotels",
            {
                "destination": "Goa",
                "nights": 3,
            },
        )

        print("\nHotel result:")
        print(hotel_result)

        # ----------------------------------------------------
        # TEST HOTEL PRICE
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("Testing hotel_price")
        print("=" * 60)

        hotel_price_result = await client.call_tool(
            "hotel_price",
            {
                "destination": "Goa",
                "nights": 3,
            },
        )

        print("\nCheapest hotel total:")
        print(hotel_price_result)

    print("\n" + "=" * 60)
    print("MCP TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
