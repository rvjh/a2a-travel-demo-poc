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
# MCP TOOLS
# ============================================================

@mcp.tool
def search_flight(destination: str) -> list[dict]:
    """
    Search available flights for a destination.
    """
    return FLIGHTS.get(destination.lower(), [])

@mcp.tool
def flight_price(destination: str) -> float:
    """
    Return the cheapest flight price for a destination.
    """

    flights = FLIGHTS.get(destination.lower(), [])

    if not flights:
        return 0.0

    return min(flight["price"] for flight in flights) 


@mcp.tool
def search_hotels(destination: str, nights: int = 2) -> list[dict]:
    """
    Search available hotels for a destination.
    """
    hotels = HOTELS.get(destination.lower(), [])
    result = []

    for hotel in hotels:
        item = hotel.copy()
        item["nights"] = nights
        result.append(item)

    return result

@mcp.tool
def hotel_price(destination: str, nights: int = 2) -> float:
    """
    Return the cheapest total hotel price.
    """
    hotels = HOTELS.get(destination.lower(), [])
    if not hotels:
        return 0.0

    return min(hotel["price_per_night"] * nights for hotel in hotels)


if __name__ == "__main__":
    # FastMCP HTTP transport uses Streamable HTTP.
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=9000,
    )

