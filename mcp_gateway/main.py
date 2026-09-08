from fastmcp import FastMCP


mcp = FastMCP("Travel MCP Gateway")


# ============================================================
# FLIGHT DATA
# ============================================================

FLIGHTS = {
    "goa": [
        {
            "airline": "IndiGo",
            "flight": "6E-123",
            "from_city": "Bengaluru",
            "to_city": "Goa",
            "price": 4500.0,
            "currency": "INR",
            "duration_hours": 1.2,
        },
        {
            "airline": "Air India",
            "flight": "AI-456",
            "from_city": "Bengaluru",
            "to_city": "Goa",
            "price": 5200.0,
            "currency": "INR",
            "duration_hours": 1.3,
        },
    ],
    "mumbai": [
        {
            "airline": "IndiGo",
            "flight": "6E-200",
            "from_city": "Bengaluru",
            "to_city": "Mumbai",
            "price": 3500.0,
            "currency": "INR",
            "duration_hours": 1.7,
        }
    ],
}


# ============================================================
# HOTEL DATA
# ============================================================

HOTELS = {
    "goa": [
        {
            "name": "Sea View Hotel",
            "destination": "Goa",
            "price_per_night": 3000.0,
            "currency": "INR",
            "rating": 4.2,
        },
        {
            "name": "Palm Resort",
            "destination": "Goa",
            "price_per_night": 4500.0,
            "currency": "INR",
            "rating": 4.6,
        },
    ],
    "mumbai": [
        {
            "name": "City Hotel",
            "destination": "Mumbai",
            "price_per_night": 5000.0,
            "currency": "INR",
            "rating": 4.1,
        }
    ],
}


# ============================================================
# FLIGHT TOOLS
# ============================================================

@mcp.tool
def search_flights(destination: str) -> list[dict]:
    """
    Search available flights for a destination.
    """
    destination = destination.strip().lower()

    return FLIGHTS.get(destination, [])


@mcp.tool
def flight_price(destination: str) -> float:
    """
    Return the cheapest flight price for a destination.
    """
    destination = destination.strip().lower()

    flights = FLIGHTS.get(destination, [])

    if not flights:
        return 0.0

    return min(
        flight["price"]
        for flight in flights
    )


# ============================================================
# HOTEL TOOLS
# ============================================================

@mcp.tool
def search_hotels(
    destination: str,
    nights: int = 2,
) -> list[dict]:
    """
    Search available hotels for a destination.
    """
    destination = destination.strip().lower()

    hotels = HOTELS.get(destination, [])

    result = []

    for hotel in hotels:
        item = hotel.copy()

        item["nights"] = nights

        item["total_price"] = (
            hotel["price_per_night"] * nights
        )

        result.append(item)

    return result


@mcp.tool
def hotel_price(
    destination: str,
    nights: int = 2,
) -> float:
    """
    Return the cheapest total hotel price.
    """
    destination = destination.strip().lower()

    hotels = HOTELS.get(destination, [])

    if not hotels:
        return 0.0

    return min(
        hotel["price_per_night"] * nights
        for hotel in hotels
    )


# ============================================================
# START MCP SERVER - Uncomment for running locally
# ============================================================

# if __name__ == "__main__":
#     print("Starting Travel MCP Server...")
#     print("MCP URL: http://127.0.0.1:9000/mcp")

#     mcp.run(
#         transport="http",
#         host="127.0.0.1",
#         port=9000,
#     )


# ============================================================
# START MCP SERVER - Uncomment for running in DOcker
# ============================================================

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=9000,
    )
