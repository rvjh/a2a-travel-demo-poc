 # Hotel Agent

 ## Overview

 The **Hotel Agent** is an independent FastAPI-based AI agent that searches for hotels using an MCP (Model Context Protocol) tool and uses an LLM to recommend the best hotel from the returned results.

 Implementation:

```
agents/hotel_agent/main.py
```

 The Hotel Agent communicates with the MCP Gateway through the `search_hotels` tool.

 The overall flow is:

```
Client / Router
      |
      | HTTP POST /
      v
Hotel Agent
      |
      | Determine destination
      | Determine nights
      v
MCP Gateway
      |
      | search_hotels
      v
Hotel Data
      |
      v
Hotel Models
      |
      v
LLM
      |
      | Recommend best hotel
      v
HotelAgentResult
      |
      v
Client / Router
```

---

 # Architecture

```
+-----------------------+
|    Client / Router    |
+-----------+-----------+
            |
            | HTTP POST /
            v
+-----------------------+
|      Hotel Agent      |
|        FastAPI        |
|                       |
|   handle_request()    |
+-----------+-----------+
            |
            | MCP
            v
+-----------------------+
|     MCP Gateway       |
|                       |
|    search_hotels      |
+-----------+-----------+
            |
            | Hotel data
            v
+-----------------------+
|      Hotel Agent      |
|                       |
|   Hotel(**hotel)      |
+-----------+-----------+
            |
            | Structured hotel data
            v
+-----------------------+
|          LLM          |
|                       |
|  Evaluate price and   |
|       rating          |
+-----------+-----------+
            |
            | Recommendation
            v
+-----------------------+
|    HotelAgentResult   |
+-----------------------+
```

---

 # API Endpoints

 The Hotel Agent exposes two endpoints:

```
GET /.well-known/agent-card.json
POST /
```

---

 # 1\. Agent Card

```
GET /.well-known/agent-card.json
```

 The Agent Card provides information about the Hotel Agent.

 It is implemented as:

```
@app.get(
    "/.well-known/agent-card.json",
    response_model=AgentCard,
)
async def agent_card():
```

 The returned `AgentCard` contains:

```
AgentCard(
    name="hotel-agent",
    description="Finds hotels for travel destinations",
    url="http://127.0.0.1:8002",
    skills=[
        "hotel_search",
        "hotel_price",
    ],
)
```

 Example response:

```
{
  "name": "hotel-agent",
  "description": "Finds hotels for travel destinations",
  "url": "http://127.0.0.1:8002",
  "skills": [
    "hotel_search",
    "hotel_price"
  ]
}
```

 The Agent Card is used for **agent discovery**.

 It does not perform a hotel search.

---

 # 2\. Hotel Request

```
POST /
```

 This is the main endpoint used to process hotel requests.

 Example request:

```
{
  "message": "Find me a hotel in Mumbai for 3 days"
}
```

 The request is validated using:

```
AgentRequest
```

 and handled by:

```
@app.post("/", response_model=HotelAgentResult)
async def handle_request(request: AgentRequest):
```

---

 # Request Processing Flow

 The Hotel Agent processes a request in the following order:

```
1. Receive request
        ↓
2. Determine destination
        ↓
3. Determine number of nights
        ↓
4. Call MCP search_hotels
        ↓
5. Receive raw hotel data
        ↓
6. Convert data to Hotel models
        ↓
7. Check whether hotels were found
        ↓
8. Create structured LLM
        ↓
9. Send request + hotel data to LLM
        ↓
10. LLM recommends a hotel
        ↓
11. Add agent/tool metadata
        ↓
12. Return HotelAgentResult
```

---

 # Step 1: Application Initialization

 When the application starts:

```
app = FastAPI(title="Hotel Agent")

llm = get_llm()
```

 The first line creates the FastAPI application.

 The second line initializes the LLM:

```
llm = get_llm()
```

 The LLM configuration is provided by:

```
common/llm.py
```

 The LLM is initialized once when the application starts.

---

 # Step 2: Receive the Request

 Suppose the client sends:

```
{
  "message": "Find me a hotel in Mumbai for 3 days"
}
```

 The request reaches:

```
handle_request()
```

 The request message is available through:

```
request.message
```

 Conceptually:

```
JSON Request
     |
     v
FastAPI
     |
     v
AgentRequest
     |
     v
handle_request()
```

---

 # Step 3: Determine Destination

 The destination initially defaults to:

```
destination = "goa"
```

 The agent then checks whether the request contains `"mumbai"`:

```
if "mumbai" in request.message.lower():
    destination = "mumbai"
```

 Therefore:

```
Message contains "mumbai"
        |
        v
destination = "mumbai"
```

 Otherwise:

```
Message does not contain "mumbai"
        |
        v
destination = "goa"
```

 ### Current behavior

```
"Find a hotel in Mumbai"
        ↓
mumbai
```

```
"Find a hotel in Goa"
        ↓
goa
```

```
"Find a hotel in Delhi"
        ↓
goa
```

```
"Find a hotel in Chennai"
        ↓
goa
```

 The current implementation therefore effectively supports:

```
Mumbai → mumbai
Everything else → goa
```

 The destination is **not currently extracted dynamically** from the user request.

---

 # Step 4: Determine Number of Nights

 The agent starts with:

```
nights = 2
```

 Therefore, the default value is:

```
2 nights
```

 The code then checks:

```
if "3 day" in request.message.lower():
    nights = 2
```

 This means that when the request contains `"3 day"`, the value remains:

```
nights = 2
```

 For example:

```
"Find a hotel in Mumbai for 3 days"
        |
        v
"3 day" detected
        |
        v
nights = 2
```

 This can represent a three-day trip with two hotel nights:

```
Day 1 → Check-in
Day 2 → Stay
Day 3 → Check-out
```

 ### Current behavior

```
Default                  → 2 nights
"3 day" in request       → 2 nights
```

 The current implementation does not dynamically extract arbitrary stay durations.

 For example, there is no separate handling for:

```
1 night
3 nights
4 nights
5 days
1 week
```

---

 # Step 5: Call the MCP Hotel Tool

 After determining:

```
destination
nights
```

 the agent calls:

```
raw_hotels = await call_mcp_hotel_tool(
    destination,
    nights,
)
```

 The MCP helper is:

```
async def call_mcp_hotel_tool(
    destination: str,
    nights: int,
) -> list[dict]:
```

---

 # Step 6: Connect to the MCP Gateway

 Inside `call_mcp_hotel_tool()`, the agent creates an MCP client:

```
async with Client(MCP_GATEWAY_URL) as client:
```

 `MCP_GATEWAY_URL` comes from:

```
from common.config import MCP_GATEWAY_URL
```

 The communication flow is:

```
Hotel Agent
     |
     | MCP Client
     v
MCP Gateway
```

---

 # Step 7: Call `search_hotels`

 The agent calls the MCP tool:

```
result = await client.call_tool(
    "search_hotels",
    {
        "destination": destination,
        "nights": nights,
    },
)
```

 For example, for:

```
destination = "mumbai"
nights = 2
```

 the MCP request is:

```
{
  "destination": "mumbai",
  "nights": 2
}
```

 The flow is:

```
Hotel Agent
     |
     | search_hotels
     | destination = mumbai
     | nights = 2
     v
MCP Gateway
     |
     v
search_hotels
     |
     v
Hotel Data
```

---

 # Step 8: Receive Hotel Data

 The MCP response is returned using:

```
return result.data
```

 The returned value is expected to be:

```
list[dict]
```

 For example:

```
[
  {
    "name": "Hotel A",
    "price": 5000,
    "rating": 4.5
  },
  {
    "name": "Hotel B",
    "price": 3500,
    "rating": 4.2
  }
]
```

 This data is stored in:

```
raw_hotels
```

---

 # Step 9: Convert Hotel Data to Models

 The raw hotel dictionaries are converted into `Hotel` models:

```
hotels = [
    Hotel(**hotel)
    for hotel in raw_hotels
]
```

 Conceptually:

```
Raw Hotel Dictionary
        |
        v
Hotel(**hotel)
        |
        v
Hotel Model
```

 For example:

```
{
    "name": "Hotel A",
    "price": 5000,
    "rating": 4.5
}
```

 becomes:

```
Hotel(
    name="Hotel A",
    price=5000,
    rating=4.5
)
```

 The resulting list is stored in:

```
hotels
```

---

 # Step 10: Check for Available Hotels

 The agent checks:

```
if not hotels:
```

 There are two possible paths.

 ## No Hotels Found

 If:

```
hotels = []
```

 the LLM is not called.

 The agent immediately returns:

```
HotelAgentResult(
    destination=destination,
    hotels=[],
    recommendation="No hotels found.",
    tools_called=["search_hotels"],
)
```

 Example response:

```
{
  "destination": "mumbai",
  "hotels": [],
  "recommendation": "No hotels found.",
  "tools_called": [
    "search_hotels"
  ]
}
```

---

 ## Hotels Found

 If hotels are available:

```
hotels = [
    Hotel(...),
    Hotel(...),
    ...
]
```

 the agent continues to the LLM.

---

 # Step 11: Create Structured LLM

 The agent creates a structured-output LLM:

```
llm_with_structure = llm.with_structured_output(
    HotelAgentResult
)
```

 This tells the LLM to return output matching the:

```
HotelAgentResult
```

 model.

 The flow is:

```
LLM
 |
 | Structured output
 v
HotelAgentResult
```

---

 # Step 12: Send Hotel Data to the LLM

 The agent calls:

```
result = llm_with_structure.invoke(
    f"""
        You are the Hotel Agent.

        User request:
        {request.message}

        Available hotels:
        {[hotel.model_dump() for hotel in hotels]}

        Recommend the best hotel.

        Rules:
        - Do not invent hotels.
        - Use only supplied hotel data.
        - Consider rating and price.
        - Return structured output.
        """
)
```

 The LLM receives:

 1. The original user request.
2. The hotels returned by the MCP tool.
3. Instructions for making the recommendation.

 The `Hotel` objects are converted into dictionaries using:

```
hotel.model_dump()
```

---

 # Step 13: LLM Recommendation

 The LLM's responsibility is to recommend the best hotel from the supplied results.

 The prompt explicitly instructs it to:

```
- Do not invent hotels.
- Use only supplied hotel data.
- Consider rating and price.
- Return structured output.
```

 Therefore, the responsibility is separated as follows:

```
MCP
 |
 | Search
 v
Hotel Data
 |
 v
LLM
 |
 | Analyze
 | Rating
 | Price
 v
Recommendation
```

 The LLM does **not** directly search for hotels.

 The MCP tool performs the hotel search.

---

 # Step 14: Add Agent and Tool Metadata

 After the LLM returns its structured result:

```
result.agent = "hotel-agent"
```

 sets the agent name.

 Then:

```
result.tools_called = ["search_hotels"]
```

 records the MCP tool used during the request.

 The final result therefore contains:

```
agent
destination
hotels
recommendation
tools_called
```

 as defined by `HotelAgentResult`.

---

 # Step 15: Return the Result

 Finally:

```
return result
```

 returns the `HotelAgentResult`.

 FastAPI serializes the result into the HTTP response.

 Conceptually:

```
{
  "agent": "hotel-agent",
  "destination": "mumbai",
  "hotels": [
    {
      "name": "Hotel A",
      "price": 5000,
      "rating": 4.5
    },
    {
      "name": "Hotel B",
      "price": 3500,
      "rating": 4.2
    }
  ],
  "recommendation": "Hotel A is the best option based on rating and price.",
  "tools_called": [
    "search_hotels"
  ]
}
```

 The exact recommendation is generated by the configured LLM.

---

 # Complete End-to-End Flow

 For this request:

```
{
  "message": "Find me a hotel in Mumbai for 3 days"
}
```

 the code executes:

```
1. Client
   |
   | POST /
   v
2. FastAPI
   |
   v
3. AgentRequest
   |
   v
4. handle_request()
   |
   v
5. destination = "goa"
   |
   | "mumbai" found
   v
6. destination = "mumbai"
   |
   v
7. nights = 2
   |
   | "3 day" found
   | nights remains 2
   v
8. call_mcp_hotel_tool("mumbai", 2)
   |
   v
9. MCP Client
   |
   | call_tool("search_hotels", ...)
   v
10. MCP Gateway
    |
    | search_hotels
    v
11. Hotel Data
    |
    v
12. Hotel(**hotel)
    |
    v
13. List[Hotel]
    |
    v
14. Check hotels
    |
    +---- No hotels
    |       |
    |       v
    |   Return HotelAgentResult
    |
    +---- Hotels found
            |
            v
15. Structured LLM
            |
            v
16. User request + hotel data
            |
            v
17. LLM evaluates rating and price
            |
            v
18. HotelAgentResult
            |
            v
19. Set agent = "hotel-agent"
            |
            v
20. Set tools_called = ["search_hotels"]
            |
            v
21. Return JSON
            |
            v
22. Client
```

---

 # Component Responsibilities

 | Component | Responsibility |
| --- | --- |
| FastAPI | Exposes the Hotel Agent HTTP API |
| `AgentRequest` | Represents the incoming request |
| `AgentCard` | Describes the Hotel Agent |
| MCP Client | Connects the agent to the MCP Gateway |
| `search_hotels` | Retrieves hotel data |
| `Hotel` | Represents structured hotel data |
| `LLM` | Recommends the best hotel |
| `HotelAgentResult` | Defines the structured response |
| `MCP_GATEWAY_URL` | Provides the MCP Gateway location |
| `get_llm()` | Initializes the LLM |

---

 # MCP and LLM Responsibilities

 The key architectural distinction is:

```
MCP = Data Retrieval
LLM = Recommendation
FastAPI = Orchestration
```

 ### MCP

 The MCP tool:

```
search_hotels
```

 is responsible for retrieving hotel options.

```
destination
     +
nights
     |
     v
search_hotels
     |
     v
Hotel Data
```

 ### LLM

 The LLM receives the returned hotel data and recommends the best option.

```
Hotel Data
     |
     v
LLM
     |
     | Consider rating and price
     v
Recommendation
```

 ### FastAPI

 The Hotel Agent coordinates the entire process:

```
Request
   ↓
Destination
   ↓
Nights
   ↓
MCP
   ↓
Hotel Models
   ↓
LLM
   ↓
HotelAgentResult
```

---

 # Current Destination Logic

 The current implementation uses:

```
destination = "goa"

if "mumbai" in request.message.lower():
    destination = "mumbai"
```

 Therefore:

```
Mumbai → mumbai
Everything else → goa
```

 This means the following request:

```
"Find a hotel in Mumbai"
```

 results in:

```
destination = "mumbai"
```

 while:

```
"Find a hotel in Delhi"
```

 results in:

```
destination = "goa"
```

 because `"delhi"` is not handled by the current destination logic.

---

 # Current Nights Logic

 The current implementation uses:

```
nights = 2

if "3 day" in request.message.lower():
    nights = 2
```

 Therefore the effective behavior is:

```
Default → 2 nights
"3 day" → 2 nights
```

 For example:

```
"Hotel in Mumbai for 3 days"
              |
              v
        destination = mumbai
        nights = 2
```

 The `"3 day"` condition does not change the value because both the default and conditional assignment are `2`.

---

 # Final Architecture

```
                         CLIENT
                           |
                           | POST /
                           v
                +---------------------+
                |     HOTEL AGENT      |
                |       FastAPI        |
                +----------+----------+
                           |
                           v
                 handle_request()
                           |
              +------------+------------+
              |                         |
              v                         v
        Destination                  Nights
          Logic                      Logic
              |                         |
              +------------+------------+
                           |
                           v
                call_mcp_hotel_tool()
                           |
                           | MCP
                           v
                +---------------------+
                |    MCP GATEWAY      |
                +----------+----------+
                           |
                           v
                    search_hotels
                           |
                           v
                    Hotel Data
                           |
                           v
                    Hotel Models
                           |
                           v
                +---------------------+
                |         LLM         |
                |                     |
                | Consider rating +   |
                | price               |
                +----------+----------+
                           |
                           v
                +---------------------+
                |  HotelAgentResult   |
                +----------+----------+
                           |
                           v
                         CLIENT
```

---

 # Summary

 The Hotel Agent performs the following sequence:

```
Receive HTTP request
        ↓
Determine destination
        ↓
Determine number of nights
        ↓
Call MCP search_hotels
        ↓
Receive hotel data
        ↓
Convert data to Hotel models
        ↓
Check for available hotels
        ↓
Create structured LLM
        ↓
Provide hotel data to LLM
        ↓
LLM evaluates rating and price
        ↓
Generate HotelAgentResult
        ↓
Add agent/tool metadata
        ↓
Return HTTP response
```

 **In short: the Hotel Agent uses MCP to retrieve hotels, uses the LLM to recommend the best hotel based on the supplied data, and uses FastAPI to expose and orchestrate the complete agent workflow.**

 This version sticks closely to the code you supplied and explicitly documents the current `"mumbai"`/`"goa"` destination behavior and the `2-night` behavior.