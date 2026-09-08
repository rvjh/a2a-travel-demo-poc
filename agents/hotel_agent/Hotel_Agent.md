# Hotel Agent

## Overview

 The **Hotel Agent** is a FastAPI-based AI agent that searches for hotels using an MCP (Model Context Protocol) tool and then uses an LLM to recommend the best hotel from the available results.

 agents/hotel_agent/main.py

 The agent receives a user's travel request, determines the destination and number of nights, calls the MCP `search_hotels` tool, converts the returned data into `Hotel` models, and finally asks the LLM to recommend the best hotel based on **rating and price**.

 The overall flow is:

```
User / Client
     |
     | POST /
     v
Hotel Agent (FastAPI)
     |
     | Determine destination
     | Determine number of nights
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
User / Client
```

---

# Architecture

 The Hotel Agent consists of three major responsibilities:

```
+-----------------------+
|        Client         |
|                       |
| "Find a hotel in      |
|       Mumbai"         |
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
| Convert data → Hotel  |
| models                |
+-----------+-----------+
            |
            | Hotel data
            v
+-----------------------+
|          LLM          |
|                       |
| Recommend best hotel  |
| based on rating/price |
+-----------+-----------+
            |
            v
+-----------------------+
|   HotelAgentResult    |
+-----------------------+
```

---

# API Endpoints

 The Hotel Agent exposes two endpoints.

## 1\. Agent Card

```
GET /.well-known/agent-card.json
```

 This endpoint provides information about the Hotel Agent.

 It tells other agents or clients:

- Agent name
- Agent description
- Agent URL
- Supported skills

 The endpoint is defined as:

```
@app.get(
    "/.well-known/agent-card.json",
    response_model=AgentCard,
)
async def agent_card():
```

 It returns:

```
return AgentCard(
    name="hotel-agent",
    description="Finds hotels for travel destinations",
    url="http://127.0.0.1:8002",
    skills=[
        "hotel_search",
        "hotel_price",
    ],
)
```

 Conceptually, the response looks like:

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

 This endpoint is mainly used for **agent discovery**.

 It does not search for hotels.

---

# 2\. Hotel Request

```
POST /
```

 This is the main endpoint that processes hotel requests.

 For example:

```
{
  "message": "Find me a hotel in Mumbai for 3 days"
}
```

 FastAPI converts this request into an:

```
AgentRequest
```

 object.

 The request is then handled by:

```
async def handle_request(
    request: AgentRequest,
):
```

---

# Complete Request Flow

 The Hotel Agent follows these steps:

```
1. Receive user request
        ↓
2. Determine destination
        ↓
3. Determine number of nights
        ↓
4. Call MCP search_hotels tool
        ↓
5. Receive raw hotel data
        ↓
6. Convert raw data to Hotel models
        ↓
7. Check if hotels exist
        ↓
8. Create structured LLM
        ↓
9. Send user request + hotel data to LLM
        ↓
10. LLM recommends best hotel
        ↓
11. Add agent/tool information
        ↓
12. Return HotelAgentResult
```

---

# Step 1: Application Startup

 When the application starts:

```
app = FastAPI(title="Hotel Agent")

llm = get_llm()
```

 The first line creates the FastAPI application.

```
FastAPI Application
       |
       +── GET /.well-known/agent-card.json
       |
       +── POST /
```

 The second line initializes the LLM:

```
llm = get_llm()
```

 The actual LLM configuration comes from:

```
common.llm
```

 The LLM object is created when the application starts, but the actual recommendation request happens later inside `handle_request()`.

---

# Step 2: Client Sends Hotel Request

 Suppose the client sends:

```
{
  "message": "I need a hotel in Mumbai for 3 days"
}
```

 to:

```
POST /
```

 FastAPI receives the request and creates an `AgentRequest` object.

 Conceptually:

```
JSON Request
     ↓
FastAPI
     ↓
AgentRequest
     ↓
handle_request()
```

 The message is available as:

```
request.message
```

 which contains:

```
I need a hotel in Mumbai for 3 days
```

---

# Step 3: Determine Destination

 The code starts with:

```
destination = "goa"
```

 So Goa is the default destination.

 Then it checks:

```
if "mumbai" in request.message.lower():
    destination = "mumbai"
```

 For:

```
"I need a hotel in Mumbai for 3 days"
```

 the code converts the message to lowercase:

```
"i need a hotel in mumbai for 3 days"
```

 Then:

```
"mumbai" in request.message.lower()
```

 returns:

```
True
```

 Therefore:

```
destination = "mumbai"
```

 The flow is:

```
User Message
     |
     v
Does message contain "mumbai"?
     |
   +---+---+
   |       |
  YES      NO
   |       |
   v       v
Mumbai    Goa
```

### Current limitation

 The destination logic currently supports only:

```
Mumbai → Mumbai
Everything else → Goa
```

 For example:

```
"Hotel in Mumbai"  → Mumbai
"Hotel in Goa"     → Goa
"Hotel in Delhi"   → Goa
"Hotel in Chennai" → Goa
"Hotel in Dubai"   → Goa
```

 The code could later be improved to extract the destination dynamically.

---

# Step 4: Determine Number of Nights

 The code starts with:

```
nights = 2
```

 So the default stay is:

```
2 nights
```

 Then it checks:

```
if "3 day" in request.message.lower():
    nights = 2
```

 For:

```
"I need a hotel in Mumbai for 3 days"
```

 the condition is true.

 However, the value is still:

```
nights = 2
```

 because the code assigns:

```
nights = 2
```

 again.

 Therefore, despite the `"3 day"` condition, the actual number of nights sent to the MCP tool remains **2**.

 The current logic is effectively:

```
Default
  ↓
2 nights

"3 day" found?
  ↓
Yes
  ↓
Still 2 nights
```

 This is likely a bug or unfinished logic.

 If the intention is:

```
3 days → 3 days
```

 or:

```
3 days → 2 nights
```

 the code should explicitly implement that conversion.

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

 For example:

```
destination = "mumbai"
nights = 2
```

 The call becomes:

```
call_mcp_hotel_tool(
    "mumbai",
    2
)
```

---

# Step 6: MCP Client Connects to Gateway

 Inside:

```
async def call_mcp_hotel_tool(
    destination: str,
    nights: int,
) -> list[dict]:
```

 the code creates an MCP client:

```
async with Client(MCP_GATEWAY_URL) as client:
```

 The gateway URL comes from:

```
from common.config import MCP_GATEWAY_URL
```

 The flow is:

```
Hotel Agent
     |
     | MCP connection
     v
MCP Gateway
```

---

# Step 7: Call `search_hotels`

 The agent then executes:

```
result = await client.call_tool(
    "search_hotels",
    {
        "destination": destination,
        "nights": nights,
    },
)
```

 For example:

```
{
  "destination": "mumbai",
  "nights": 2
}
```

 The complete MCP flow is:

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

# Step 8: Receive Raw Hotel Data

 The MCP result is returned using:

```
return result.data
```

 For example, the MCP tool could return:

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

 At this point:

```
MCP
 ↓
result.data
 ↓
raw_hotels
```

---

# Step 9: Convert Raw Data to Hotel Models

 The code then executes:

```
hotels = [
    Hotel(**hotel)
    for hotel in raw_hotels
]
```

 Each dictionary is converted into a `Hotel` object.

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

 The flow is:

```
Raw Hotel Dictionary
        |
        v
Hotel(**hotel)
        |
        v
Hotel Pydantic Model
```

 If the MCP returns three hotels:

```
raw_hotels
   |
   +── Hotel 1 → Hotel(...)
   |
   +── Hotel 2 → Hotel(...)
   |
   +── Hotel 3 → Hotel(...)
```

 Now:

```
hotels
```

 contains a list of validated `Hotel` objects.

---

# Step 10: Check Whether Hotels Exist

 The code checks:

```
if not hotels:
```

 There are two possible paths.

## Case A: No hotels

 If:

```
hotels = []
```

 the condition is true.

 The agent returns:

```
HotelAgentResult(
    destination=destination,
    hotels=[],
    recommendation="No hotels found.",
    tools_called=["search_hotels"],
)
```

 The response is conceptually:

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

 The LLM is **not called** in this case.

---

## Case B: Hotels are available

 If:

```
hotels = [
    Hotel(...),
    Hotel(...),
    Hotel(...)
]
```

 then:

```
not hotels
```

 is false.

 The code continues to the LLM.

---

# Step 11: Prepare Structured LLM

 The code creates:

```
llm_with_structure = llm.with_structured_output(
    HotelAgentResult
)
```

 This tells the LLM to return data matching:

```
HotelAgentResult
```

 rather than arbitrary text.

 Conceptually:

```
Normal LLM
   ↓
Free-form response

Structured LLM
   ↓
HotelAgentResult
```

 This helps keep the final response consistent with your API model.

---

# Step 12: Send Hotel Data to the LLM

 The LLM receives:

### User request

```
request.message
```

 For example:

```
I need a hotel in Mumbai for 3 days
```

### Available hotels

 The code uses:

```
[hotel.model_dump() for hotel in hotels]
```

 This converts the `Hotel` models into dictionaries.

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

 The LLM receives a prompt conceptually like:

```
You are the Hotel Agent.

User request:
I need a hotel in Mumbai for 3 days

Available hotels:
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

Recommend the best hotel.

Rules:
- Do not invent hotels.
- Use only supplied hotel data.
- Consider rating and price.
- Return structured output.
```

---

# Step 13: LLM Recommends the Best Hotel

 The LLM now analyzes only the hotels supplied by the MCP tool.

 For example:

```
Hotel A
Rating: 4.5
Price: ₹5000

Hotel B
Rating: 4.2
Price: ₹3500
```

 The LLM could recommend Hotel A because it has the higher rating.

 Or it could recommend Hotel B if it determines that the lower price provides better value.

 The important part is:

```
MCP → Finds hotels
LLM → Recommends a hotel
```

 The LLM does **not** directly search the hotel database in this code.

---

# Step 14: Add Agent Information

 After the LLM returns a structured result:

```
result.agent = "hotel-agent"
```

 sets:

```
agent = "hotel-agent"
```

 Then:

```
result.tools_called = ["search_hotels"]
```

 records the MCP tool that was used.

---

# Step 15: Return Final Result

 Finally:

```
return result
```

 returns the `HotelAgentResult`.

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
  "recommendation": "Hotel A is the best choice because it has the highest rating.",
  "tools_called": [
    "search_hotels"
  ]
}
```

 FastAPI then serializes this into the HTTP response.

---

# Complete End-to-End Example

 Suppose the client sends:

```
{
  "message": "Find me a hotel in Mumbai for 3 days"
}
```

 The execution is:

```
1. Client
   |
   | POST /
   v
2. FastAPI
   |
   v
3. handle_request()
   |
   | request.message
   | = "Find me a hotel in Mumbai for 3 days"
   v
4. Set destination
   |
   | Default = Goa
   |
   | "mumbai" found
   |
   v
   destination = Mumbai
   |
   v
5. Set nights
   |
   | Default = 2
   |
   | "3 day" found
   |
   | nights = 2
   v
6. call_mcp_hotel_tool(
       "mumbai",
       2
   )
   |
   v
7. MCP Client
   |
   | call_tool()
   v
8. MCP Gateway
   |
   | search_hotels
   | {
   |   destination: "mumbai",
   |   nights: 2
   | }
   v
9. Hotel Search Tool
   |
   v
10. Raw Hotel Data
    |
    v
11. Hotel(**hotel)
    |
    v
12. List[Hotel]
    |
    v
13. Are hotels available?
    |
    +------ No ------→ Return "No hotels found."
    |
    |
    +------ Yes
             |
             v
14. Create structured LLM
             |
             v
15. Send user request + hotel data
             |
             v
16. LLM evaluates hotels
             |
             | Rating
             | Price
             v
17. Best hotel recommendation
             |
             v
18. HotelAgentResult
             |
             v
19. agent = "hotel-agent"
             |
             v
20. tools_called = ["search_hotels"]
             |
             v
21. Return JSON
             |
             v
22. Client
```

---

# Complete Architecture

```
                         CLIENT
                           |
                           |
                    POST / request
                           |
                           v
                +---------------------+
                |     HOTEL AGENT      |
                |       FastAPI        |
                +----------+----------+
                           |
                           v
                 handle_request()
                           |
                +----------+----------+
                |                     |
                v                     v
          Destination             Nights
          extraction              extraction
                |                     |
                +----------+----------+
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
                           |
                    search_hotels
                           |
                           v
                +---------------------+
                |    Hotel Search     |
                |       Tool          |
                +----------+----------+
                           |
                           | Hotel data
                           v
                +---------------------+
                |   Hotel Pydantic    |
                |       Models        |
                +----------+----------+
                           |
                           | Validated data
                           v
                +---------------------+
                |         LLM         |
                |                     |
                | Evaluate price +    |
                | rating              |
                +----------+----------+
                           |
                           | Recommendation
                           v
                +---------------------+
                | HotelAgentResult    |
                +----------+----------+
                           |
                           v
                         CLIENT
```

---

# Responsibility of Each Component

| Component            | Responsibility                      |
| -------------------- | ----------------------------------- |
| FastAPI              | Exposes HTTP endpoints              |
| `AgentRequest`     | Validates incoming request          |
| `AgentCard`        | Describes the Hotel Agent           |
| MCP Client           | Connects to MCP Gateway             |
| `search_hotels`    | Retrieves hotel information         |
| `Hotel`            | Represents a hotel                  |
| LLM                  | Recommends the best available hotel |
| `HotelAgentResult` | Defines final response structure    |
| `MCP_GATEWAY_URL`  | Defines MCP Gateway location        |
| `get_llm()`        | Creates/configures the LLM          |

---

# MCP vs LLM Responsibilities

 The most important architectural concept is the separation between **tool execution** and **reasoning**.

```
                 HOTEL AGENT
                     |
          +----------+----------+
          |                     |
          v                     v
         MCP                   LLM
          |                     |
          v                     v
  Search actual hotels     Analyze hotels
          |                     |
          v                     v
    Hotel information      Recommendation
          |                     |
          +----------+----------+
                     |
                     v
              Final Response
```

### MCP

 MCP is responsible for:

```
"Find hotels in Mumbai for 2 nights."
```

 It returns actual hotel data.

### LLM

 The LLM is responsible for:

```
"Given these hotels, which one is the best?"
```

 It analyzes:

```
Price
Rating
User request
```

 and produces the recommendation.

### FastAPI Agent

 The Hotel Agent coordinates everything:

```
Receive request
      ↓
Determine parameters
      ↓
Call MCP
      ↓
Get hotel data
      ↓
Call LLM
      ↓
Return structured response
```

---

# Important Issue in the Current Code

 There is a suspicious piece of logic:

```
nights = 2

if "3 day" in request.message.lower():
    nights = 2
```

 Both branches set `nights` to `2`.

 Therefore:

```
User: "hotel for 3 days"
             ↓
"3 day" detected
             ↓
nights = 2
```

 So the condition currently has **no effect**.

 If your intention is that:

```
3 days → 2 nights
```

 then the current code is actually correct from a hotel-stay perspective, because a 3-day trip can represent 2 hotel nights.

 For example:

```
Day 1 → Check-in
Day 2 → Stay
Day 3 → Check-out
```

 means:

```
2 nights
```

 If instead you mean:

```
3 days → 3 hotel nights
```

 then it should be:

```
if "3 day" in request.message.lower():
    nights = 3
```

 So the intended business meaning needs to be clear.

---

# Current Limitations

 The current destination extraction is hard-coded:

```
destination = "goa"

if "mumbai" in request.message.lower():
    destination = "mumbai"
```

 This means:

```
Mumbai → Mumbai
Anything else → Goa
```

 Similarly, the nights extraction only recognizes:

```
"3 day"
```

 and doesn't dynamically handle:

```
1 night
2 nights
3 nights
5 nights
one week
4 days
weekend
```

 A more scalable design would be:

```
User Request
     |
     v
LLM / Request Parser
     |
     +---- destination
     |
     +---- check-in
     |
     +---- check-out
     |
     +---- number of nights
     |
     +---- budget
     |
     v
MCP search_hotels
     |
     v
Hotel Results
     |
     v
LLM Recommendation
     |
     v
HotelAgentResult
```

---

# Final Summary

 The Hotel Agent follows this pipeline:

```
User
  ↓
FastAPI
  ↓
AgentRequest
  ↓
Extract destination
  ↓
Extract nights
  ↓
MCP Client
  ↓
MCP Gateway
  ↓
search_hotels
  ↓
Raw hotel data
  ↓
Hotel Pydantic models
  ↓
Check if hotels exist
  ↓
Structured LLM
  ↓
Evaluate price + rating
  ↓
Hotel recommendation
  ↓
HotelAgentResult
  ↓
FastAPI JSON response
  ↓
User
```

 **In one sentence:**

> The Hotel Agent receives a travel request, determines the destination and number of nights, uses the MCP `search_hotels` tool to retrieve real hotel options, converts them into `Hotel` models, passes those options to the LLM for a price-and-rating-based recommendation, and returns the result as a structured `HotelAgentResult`.
