# Flight Agent

 ## Overview

Flight Agent
The Flight Agent is an independent HTTP service.

It communicates with the MCP Gateway.

agents/flight_agent/main.py

The flow is now:

Router
   |
   | HTTP / A2A
   v
Flight Agent
   |
   | MCP
   v
MCP Gateway
   |
   v
search_flights
   |
   v
Flight Agent
   |
   v
LLM


 The **Flight Agent** is a FastAPI-based AI agent that searches for flights using an MCP (Model Context Protocol) tool and then uses an LLM to recommend the best available flight.

 The overall flow is:

```
User / Client
     |
     | POST /
     v
Flight Agent (FastAPI)
     |
     | Determine destination
     v
MCP Gateway
     |
     | search_flights
     v
Flight Data
     |
     v
Flight Models
     |
     v
LLM
     |
     | Recommend best flight
     v
FlightAgentResult
     |
     v
User / Client
```

---

 ## Architecture

 The Flight Agent has three main components:

```
+-----------------------+
|        Client         |
|                       |
| "Find flights to      |
|        Mumbai"        |
+-----------+-----------+
            |
            | HTTP POST /
            v
+-----------------------+
|     Flight Agent     |
|       FastAPI        |
|                       |
|  handle_request()    |
+-----------+-----------+
            |
            | MCP
            v
+-----------------------+
|     MCP Gateway      |
|                       |
|   search_flights     |
+-----------+-----------+
            |
            | Flight data
            v
+-----------------------+
|     Flight Agent     |
|                       |
| Convert to Flight    |
| models               |
+-----------+-----------+
            |
            | Flight data
            v
+-----------------------+
|         LLM           |
|                       |
| Recommend best       |
| flight               |
+-----------+-----------+
            |
            v
+-----------------------+
|  FlightAgentResult   |
+-----------------------+
```

---

 # API Endpoints

 The application exposes two endpoints.

 ## 1\. Agent Card

```
GET /.well-known/agent-card.json
```

 This endpoint provides information about the Flight Agent.

 It tells other agents or clients:

 - Agent name
- Agent description
- Agent URL
- Supported skills

 Example response:

```
{
  "name": "flight-agent",
  "description": "Finds flights for travel destinations",
  "url": "http://127.0.0.1:8001",
  "skills": [
    "flight_search",
    "flight_price"
  ]
}
```

 This endpoint is mainly used for **agent discovery**.

 It does not perform a flight search.

---

 # 2\. Flight Request

```
POST /
```

 This is the main endpoint used to process flight requests.

 Example request:

```
{
  "message": "Find me a flight to Mumbai"
}
```

 The request is converted by FastAPI into an `AgentRequest` object.

```
async def handle_request(
    request: AgentRequest,
):
```

---

 # Complete Request Flow

 ## Step 1: Client sends a request

 The client sends:

```
{
  "message": "Find me a flight to Mumbai"
}
```

 to:

```
POST /
```

 The request reaches:

```
handle_request()
```

---

 ## Step 2: Determine the destination

 The agent initially sets:

```
destination = "goa"
```

 So Goa is the default destination.

 Then it checks:

```
if "mumbai" in request.message.lower():
    destination = "mumbai"
```

 For this request:

```
"Find me a flight to Mumbai"
```

 the check becomes:

```
"mumbai" in "find me a flight to mumbai"
```

 which is `True`.

 Therefore:

```
destination = "mumbai"
```

 The current implementation supports:

```
Mumbai → mumbai
Everything else → goa
```

 For example:

```
"Find flights to Mumbai"
        ↓
destination = mumbai
```

 and:

```
"Find flights to Goa"
        ↓
destination = goa
```

---

 # Step 3: Call the MCP Flight Tool

 After determining the destination, the agent calls:

```
raw_flights = await call_mcp_flight_tool(
    destination
)
```

 The function:

```
async def call_mcp_flight_tool(
    destination: str,
) -> list[dict]:
```

 creates an MCP client:

```
async with Client(MCP_GATEWAY_URL) as client:
```

 The client connects to the configured:

```
MCP_GATEWAY_URL
```

---

 # Step 4: Execute `search_flights`

 The agent calls the MCP tool:

```
result = await client.call_tool(
    "search_flights",
    {
        "destination": destination,
    },
)
```

 For Mumbai, the MCP request is effectively:

```
{
  "destination": "mumbai"
}
```

 The flow is:

```
Flight Agent
     |
     | call_tool()
     v
MCP Gateway
     |
     | search_flights
     v
Flight Search Tool
     |
     v
Flight Data
```

---

 # Step 5: Receive Flight Data

 The MCP tool returns the result.

 The agent gets the data using:

```
return result.data
```

 For example:

```
[
    {
        "airline": "IndiGo",
        "flight_number": "6E123",
        "price": 4500
    },
    {
        "airline": "Air India",
        "flight_number": "AI456",
        "price": 5200
    }
]
```

 This raw data is stored in:

```
raw_flights
```

---

 # Step 6: Convert Data to Flight Models

 The raw dictionaries are converted into `Flight` objects:

```
flights = [
    Flight(**flight)
    for flight in raw_flights
]
```

 For example:

```
{
    "airline": "IndiGo",
    "flight_number": "6E123",
    "price": 4500
}
```

 becomes:

```
Flight(
    airline="IndiGo",
    flight_number="6E123",
    price=4500
)
```

 The purpose of this step is to convert unstructured dictionary data into validated application models.

 The flow becomes:

```
Raw MCP Data
     |
     v
Flight(**flight)
     |
     v
Flight Object
```

---

 # Step 7: Check Whether Flights Were Found

 The agent checks:

```
if not flights:
```

 If the list is empty:

```
flights = []
```

 the LLM is not called.

 Instead, the agent immediately returns:

```
FlightAgentResult(
    destination=destination,
    flights=[],
    recommendation="No flights found.",
    tools_called=["search_flights"],
)
```

 The response will be similar to:

```
{
  "destination": "mumbai",
  "flights": [],
  "recommendation": "No flights found.",
  "tools_called": [
    "search_flights"
  ]
}
```

---

 # Step 8: Prepare the LLM

 If flights are available, the agent creates a structured LLM:

```
llm_with_structure = llm.with_structured_output(
    FlightAgentResult
)
```

 This tells the LLM that its response should follow the structure defined by:

```
FlightAgentResult
```

 Instead of returning arbitrary text, the LLM should produce structured flight-agent output.

---

 # Step 9: Send Flight Data to the LLM

 The agent sends two important pieces of information to the LLM:

 ### User request

```
request.message
```

 Example:

```
Find me a flight to Mumbai
```

 ### Available flights

```
[flight.model_dump() for flight in flights]
```

 This converts the `Flight` objects back into dictionaries for inclusion in the LLM prompt.

 The LLM receives information conceptually like:

```
You are the Flight Agent.

User request:
Find me a flight to Mumbai

Available flights:
[
    {
        "airline": "IndiGo",
        "flight_number": "6E123",
        "price": 4500
    },
    {
        "airline": "Air India",
        "flight_number": "AI456",
        "price": 5200
    }
]

Recommend the best flight.

Rules:
- Do not invent flights.
- Use only the supplied flight data.
- Keep the recommendation short.
- Return destination, flights and recommendation.
```

---

 # Step 10: LLM Recommends a Flight

 The LLM analyzes the supplied flights.

 For example:

```
IndiGo
Flight: 6E123
Price: ₹4500

Air India
Flight: AI456
Price: ₹5200
```

 The LLM may determine that:

```
IndiGo 6E123 is the best option because it has the lower price.
```

 The important point is that the LLM is **not searching for flights**.

 The MCP tool searches for flights.

 The LLM only analyzes the flight data supplied by the MCP tool.

```
MCP
 |
 | Find flights
 v
Flight Data
 |
 | Give data to LLM
 v
LLM
 |
 | Recommend
 v
Final Result
```

---

 # Step 11: Add Agent Information

 After the LLM returns the structured result:

```
result.agent = "flight-agent"
```

 sets the agent name.

 Then:

```
result.tools_called = ["search_flights"]
```

 records which MCP tool was used.

 The final object is conceptually:

```
{
  "agent": "flight-agent",
  "destination": "mumbai",
  "flights": [
    {
      "airline": "IndiGo",
      "flight_number": "6E123",
      "price": 4500
    },
    {
      "airline": "Air India",
      "flight_number": "AI456",
      "price": 5200
    }
  ],
  "recommendation": "IndiGo 6E123 is the best option.",
  "tools_called": [
    "search_flights"
  ]
}
```

---

 # Step 12: Return the Response

 Finally:

```
return result
```

 returns the `FlightAgentResult` to the client.

 FastAPI automatically serializes the Pydantic model into JSON.

```
FlightAgentResult
       |
       v
FastAPI serialization
       |
       v
JSON response
       |
       v
Client
```

---

 # End-to-End Example

 Suppose the user sends:

```
{
  "message": "I need a flight to Mumbai"
}
```

 The complete execution is:

```
1. Client
   |
   | POST /
   | message = "I need a flight to Mumbai"
   v
2. FastAPI
   |
   v
3. handle_request()
   |
   | destination = "goa"
   |
   | Check message for "mumbai"
   |
   v
4. destination = "mumbai"
   |
   v
5. call_mcp_flight_tool("mumbai")
   |
   v
6. MCP Client
   |
   | call_tool(
   |   "search_flights",
   |   {"destination": "mumbai"}
   | )
   v
7. MCP Gateway
   |
   v
8. search_flights
   |
   v
9. Raw flight data
   |
   v
10. Flight(**flight)
    |
    v
11. List[Flight]
    |
    v
12. Check flights
    |
    +---- No flights
    |       |
    |       v
    |   Return "No flights found."
    |
    +---- Flights found
            |
            v
13. Create structured LLM
            |
            v
14. Send user request + flights
            |
            v
15. LLM recommends best flight
            |
            v
16. FlightAgentResult
            |
            v
17. Set agent = "flight-agent"
            |
            v
18. Set tools_called = ["search_flights"]
            |
            v
19. Return JSON
            |
            v
20. Client
```

---

 # Responsibility of Each Component

 | Component | Responsibility |
| --- | --- |
| FastAPI | Exposes HTTP endpoints |
| `AgentRequest` | Validates incoming request |
| `AgentCard` | Describes the Flight Agent |
| `MCP Client` | Connects to the MCP Gateway |
| `search_flights` | Retrieves flight information |
| `Flight` | Represents a flight |
| `LLM` | Recommends the best supplied flight |
| `FlightAgentResult` | Defines the final response structure |
| `MCP_GATEWAY_URL` | Configures the MCP Gateway location |

---

 # Important Design Point

 The application follows an **agent orchestration pattern**:

```
                  Flight Agent
                       |
          +------------+------------+
          |                         |
          v                         v
     MCP Tool                     LLM
          |                         |
          |                         |
   Get actual data          Analyze data
          |                         |
          +------------+------------+
                       |
                       v
                Final Response
```

 The responsibilities are separated:

 ### MCP = Tool execution

```
"Find me available flights"
```

 is handled by:

```
search_flights
```

 ### LLM = Reasoning/recommendation

```
"Which of these flights is the best?"
```

 is handled by:

```
LLM
```

 ### FastAPI = Agent interface/orchestration

```
"Receive request → call tools → call LLM → return result"
```

---

 # Current Limitation

 The destination detection is currently hard-coded:

```
destination = "goa"

if "mumbai" in request.message.lower():
    destination = "mumbai"
```

 Therefore:

```
"Flight to Mumbai" → Mumbai
"Flight to Goa"    → Goa
"Flight to Delhi"  → Goa ❌
"Flight to Chennai"→ Goa ❌
"Flight to Dubai"  → Goa ❌
```

 A better architecture would be to let the LLM or a dedicated parser extract the destination:

```
User message
     |
     v
Destination Extraction
     |
     +---- Mumbai
     +---- Goa
     +---- Delhi
     +---- Chennai
     +---- Bangalore
     +---- etc.
     |
     v
MCP search_flights
```

 That would make the Flight Agent much more scalable.

---

 # Summary

 The Flight Agent's complete flow is:

```
HTTP Request
     ↓
FastAPI
     ↓
AgentRequest
     ↓
Extract destination
     ↓
MCP Client
     ↓
MCP Gateway
     ↓
search_flights
     ↓
Raw flight data
     ↓
Flight Pydantic models
     ↓
Check whether flights exist
     ↓
    ┌───────────────┐
    │               │
 No flights     Flights found
    │               │
    ↓               ↓
Return "No       Structured LLM
flights"             ↓
                  Analyze flights
                     ↓
                 Recommendation
                     ↓
              FlightAgentResult
                     ↓
                Add agent info
                     ↓
                 JSON response
                     ↓
                   Client
```

 **In short: MCP gets the flight data; the LLM recommends a flight; FastAPI coordinates the entire process.**