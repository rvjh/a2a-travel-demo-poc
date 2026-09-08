# Travel MCP Gateway

## Overview

 The **Travel MCP Gateway** is the **tool layer** of the travel planning system.

 It is **not an agent**. It provides deterministic tools that can be called by the Flight Agent and Hotel Agent through **MCP (Model Context Protocol)**.

 The gateway contains predefined flight and hotel data and exposes tools for:

- Searching flights.
- Getting the cheapest flight price.
- Searching hotels.
- Calculating the cheapest hotel price.

```
Flight Agent ──┐
               |
Hotel Agent ───┤
               |
               v
        +---------------+
        |  MCP Gateway  |
        |               |
        | Flight Tools  |
        | Hotel Tools   |
        +-------+-------+
                |
                v
         Travel Data
```

---

## Main Responsibility

 The MCP Gateway is responsible for **tool execution**, not decision-making.

```
Agent
  |
  | "Find flights to Goa"
  v
MCP Gateway
  |
  v
search_flights()
  |
  v
Flight Data
```

 The agents decide **what they need**. The MCP Gateway simply executes the requested tool and returns the result.

---

## MCP Tools

### Flight Tools

#### `search_flights`

 Searches available flights for a destination.

```
search_flights(destination: str)
```

 Example:

```
search_flights("goa")
```

 Returns available flights including:

- Airline
- Flight number
- From/to cities
- Price
- Currency
- Duration

#### `flight_price`

 Returns the cheapest flight price for a destination.

```
flight_price(destination: str)
```

 Example:

```
flight_price("goa")
→ 4500.0
```

---

### Hotel Tools

#### `search_hotels`

 Searches available hotels and calculates the total price based on the number of nights.

```
search_hotels(
    destination: str,
    nights: int = 2
)
```

 Example:

```
search_hotels("goa", 2)
```

 The result includes:

- Hotel name
- Destination
- Price per night
- Rating
- Number of nights
- Total price

#### `hotel_price`

 Returns the cheapest total hotel price.

```
hotel_price(
    destination: str,
    nights: int = 2
)
```

 Example:

```
hotel_price("goa", 2)
→ 6000.0
```

---

## Deterministic Data

 The gateway currently uses predefined data:

```
FLIGHTS = {
    "goa": [...],
    "mumbai": [...]
}

HOTELS = {
    "goa": [...],
    "mumbai": [...]
}
```

 This makes the MCP tools deterministic and predictable.

 For example:

```
Goa
 ├── IndiGo
 ├── Air India
 ├── Sea View Hotel
 └── Palm Resort
```

 There is no LLM reasoning inside the MCP Gateway.

---

## MCP vs Agent

 The main difference is:

```
Agent
  |
  +--> Understand request
  +--> Make decisions
  +--> Recommend
  +--> Coordinate
```

 while:

```
MCP Gateway
  |
  +--> Expose tools
  +--> Validate inputs
  +--> Execute tools
  +--> Return data
```

 So:

> **Agent = reasoning and decision-making**

> **MCP = tools and deterministic execution**

---

## MCP Server

 The server is created with:

```
mcp = FastMCP("Travel MCP Gateway")
```

 The tools are registered using:

```
@mcp.tool
```

 For example:

```
@mcp.tool
def search_flights(destination: str):
    ...
```

 This makes `search_flights` available as an MCP tool.

---

## Starting the MCP Server

 The important part is:

```
mcp.run(
    transport="http",
    host="127.0.0.1",
    port=9000,
)
```

 This starts the MCP server using HTTP transport.

 The MCP endpoint is:

```
http://127.0.0.1:9000/mcp
```

 Current FastMCP documentation refers to this HTTP-based transport as **Streamable HTTP**.

---

## Overall System Flow

```
                         User
                           |
                           v
                  Travel Router Agent
                           |
                    +------+------+
                    |             |
                    v             v
              Flight Agent   Hotel Agent
                    |             |
                    | MCP         | MCP
                    v             v
              +-----------------------+
              |     MCP Gateway      |
              +-----------+-----------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
        Flight Tools            Hotel Tools
              |                       |
              v                       v
        Flight Data              Hotel Data
```

## Key Takeaway

 The **MCP Gateway is the tool layer** of the system. It exposes deterministic flight and hotel tools through MCP, while the Flight, Hotel, and Router Agents handle the **reasoning, orchestration, and recommendations**.

 **MCP Endpoint:**

```
http://127.0.0.1:9000/mcp
```
