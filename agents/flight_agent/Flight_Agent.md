Yes. Based strictly on the code you provided, the README should reflect the **actual implementation**, especially the fact that the destination logic currently supports only **Mumbai explicitly, with Goa as the default**.

 Here is a cleaner README version:

 Flight Agent README

# Flight Agent

## Overview

 The **Flight Agent** is an independent FastAPI HTTP service that searches for flights through an MCP Gateway and uses an LLM to recommend the best available flight.

 The implementation is located at:

```
agents/flight_agent/main.py
```

 The Flight Agent has three primary responsibilities:

- Receive flight requests over HTTP.
- Call the MCP Gateway's `search_flights` tool.
- Use the LLM to recommend a flight from the returned flight data.

 The overall flow is:

```
Client / Router
      |
      | HTTP POST /
      v
Flight Agent
      |
      | MCP
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
      | Recommendation
      v
FlightAgentResult
```

---

## Architecture

```
+-----------------------+
|    Client / Router    |
+-----------+-----------+
            |
            | HTTP POST /
            v
+-----------------------+
|     Flight Agent      |
|        FastAPI        |
|                       |
|   handle_request()    |
+-----------+-----------+
            |
            | MCP Client
            v
+-----------------------+
|     MCP Gateway       |
|                       |
|   search_flights      |
+-----------+-----------+
            |
            | Flight data
            v
+-----------------------+
|     Flight Agent      |
|                       |
|  Flight(**flight)     |
+-----------+-----------+
            |
            | Structured data
            v
+-----------------------+
|          LLM          |
|                       |
| Recommend best flight |
+-----------+-----------+
            |
            v
+-----------------------+
|   FlightAgentResult   |
+-----------------------+
```

---

# API Endpoints

 The Flight Agent exposes three endpoints:

- `GET /health`
- `GET /.well-known/agent-card.json`
- `POST /`

---

## 1\. Health Check

```
GET /health
```

 The health endpoint verifies that the Flight Agent service is running.

 It returns:

```
{
  "status": "ok",
  "agent": "flight-agent",
  "mcp_gateway": "..."
}
```

 The `mcp_gateway` value comes from:

```
MCP_GATEWAY_URL
```

 which is configured through the shared configuration.

---

## 2\. Agent Card

```
GET /.well-known/agent-card.json
```

 The Agent Card provides information about the Flight Agent for agent discovery.

 The implementation returns:

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

 The Agent Card is created using the shared:

```
AgentCard
```

 model.

 This endpoint does **not** perform a flight search.

---

## 3\. Flight Request

```
POST /
```

 This is the main endpoint of the Flight Agent.

 The request uses the:

```
AgentRequest
```

 model.

 Example:

```
{
  "message": "Find me a flight to Mumbai"
}
```

 The request is handled by:

```
@app.post("/", response_model=FlightAgentResult)
async def handle_request(request: AgentRequest):
```

---

# Request Flow

## Step 1: Receive the Request

 The client sends:

```
{
  "message": "Find me a flight to Mumbai"
}
```

 The request is received by:

```
handle_request()
```

 FastAPI validates the request using:

```
AgentRequest
```

---

## Step 2: Determine the Destination

 The current implementation uses simple string matching.

 The destination initially defaults to:

```
destination = "goa"
```

 The request message is converted to lowercase:

```
message = request.message.lower()
```

 The code then checks for Mumbai:

```
if "mumbai" in message:
    destination = "mumbai"
```

 Therefore, the current behavior is:

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

### Current destination behavior

| User request                | Destination |
| --------------------------- | ----------- |
| `Find a flight to Mumbai` | `mumbai`  |
| `I need to visit Mumbai`  | `mumbai`  |
| `Find flights to Goa`     | `goa`     |
| `Find flights to Delhi`   | `goa`     |
| `Find flights to Chennai` | `goa`     |

 This is important because the current implementation does **not** dynamically extract arbitrary destinations.

---

# Step 3: Call the MCP Gateway

 After determining the destination, the Flight Agent calls:

```
raw_flights = await call_mcp_flight_tool(destination)
```

 The MCP helper is:

```
async def call_mcp_flight_tool(destination: str) -> list[dict]:
```

 It creates an MCP client using:

```
async with Client(MCP_GATEWAY_URL) as client:
```

 The MCP Gateway URL comes from:

```
MCP_GATEWAY_URL
```

---

# Step 4: Call `search_flights`

 The MCP client calls:

```
result = await client.call_tool(
    "search_flights",
    {
        "destination": destination,
    },
)
```

 The tool name must match the MCP Gateway tool exactly:

```
search_flights
```

 For a Mumbai request, the MCP call is:

```
{
  "destination": "mumbai"
}
```

 The request flow is:

```
Flight Agent
     |
     | MCP call
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

# Step 5: Receive MCP Data

 The MCP result is returned using:

```
return result.data
```

 The returned value is expected to be a list of dictionaries:

```
list[dict]
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

 This data is stored in:

```
raw_flights
```

---

# Step 6: Convert MCP Data to Flight Models

 The raw dictionaries are converted into `Flight` models:

```
flights = [
    Flight(**flight)
    for flight in raw_flights
]
```

 Conceptually:

```
MCP dictionary
      |
      v
Flight(**flight)
      |
      v
Flight model
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

 The `Flight` model provides structured and validated flight data for the rest of the application.

---

# Step 7: Handle No Flights

 The agent checks whether any flights were returned:

```
if not flights:
```

 If there are no flights, the LLM is **not called**.

 Instead, the agent immediately returns:

```
FlightAgentResult(
    agent="flight-agent",
    destination=destination,
    flights=[],
    recommendation="No flights found.",
    tools_called=["search_flights"],
)
```

 Example response:

```
{
  "agent": "flight-agent",
  "destination": "mumbai",
  "flights": [],
  "recommendation": "No flights found.",
  "tools_called": [
    "search_flights"
  ]
}
```

---

# Step 8: Create a Structured LLM

 When flights are available, the agent creates a structured-output LLM:

```
llm_with_structure = llm.with_structured_output(
    FlightAgentResult
)
```

 The LLM is configured through:

```
llm = get_llm()
```

 from:

```
common.llm
```

 The structured output is based on:

```
FlightAgentResult
```

 This means the LLM is expected to return data matching the application's result model rather than arbitrary text.

---

# Step 9: Send Flight Data to the LLM

 The agent sends the following information to the LLM:

- The original user request.
- The available flights.

 The prompt contains:

```
You are the Flight Agent.

User request:
{request.message}

Available flights:
{available flights}

Recommend the best flight.

Rules:
- Do not invent flights.
- Use only the supplied flight data.
- Keep the recommendation short.
- Return destination, flights and recommendation.
```

 The available `Flight` models are converted back into dictionaries using:

```
flight.model_dump()
```

 The LLM therefore receives the actual flight data returned by the MCP tool.

---

# Step 10: LLM Recommendation

 The LLM's responsibility is to **recommend** a flight.

 It does not search for flights.

 The MCP tool performs the search:

```
MCP
 |
 | Search
 v
Flight Data
```

 The LLM analyzes the returned data:

```
Flight Data
 |
 | Analyze
 v
LLM
 |
 | Recommend
 v
Best Flight
```

 For example, if the MCP Gateway returns:

```
IndiGo 6E123  - ₹4500
Air India AI456 - ₹5200
```

 the LLM may recommend the IndiGo flight based on the supplied information.

 The LLM must follow the rule:

```
Do not invent flights.
```

 Therefore, recommendations should only be based on the flight data returned by `search_flights`.

---

# Step 11: Add Agent and Tool Metadata

 After the LLM returns the structured result, the agent adds its own metadata:

```
result.agent = "flight-agent"
```

 and:

```
result.tools_called = ["search_flights"]
```

 This records:

- Which agent produced the response.
- Which MCP tool was used.

---

# Step 12: Return the Result

 The final result is returned:

```
return result
```

 Because the endpoint declares:

```
response_model=FlightAgentResult
```

 FastAPI returns the structured result as JSON.

 The complete response conceptually looks like:

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

# Complete End-to-End Flow

 For a request such as:

```
{
  "message": "Find me a flight to Mumbai"
}
```

 the execution is:

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
5. Determine destination
   |
   | "mumbai" detected
   v
6. destination = "mumbai"
   |
   v
7. call_mcp_flight_tool("mumbai")
   |
   v
8. MCP Client
   |
   | call_tool("search_flights", ...)
   v
9. MCP Gateway
   |
   v
10. search_flights
    |
    v
11. Raw flight data
    |
    v
12. Flight models
    |
    v
13. Check flights
    |
    +---- No flights
    |       |
    |       v
    |   Return result
    |
    +---- Flights found
            |
            v
14. Structured LLM
            |
            v
15. User request + flight data
            |
            v
16. LLM recommendation
            |
            v
17. FlightAgentResult
            |
            v
18. Add agent/tool metadata
            |
            v
19. Return JSON
            |
            v
20. Client
```

---

# Component Responsibilities

| Component             | Responsibility                           |
| --------------------- | ---------------------------------------- |
| FastAPI               | Exposes the Flight Agent HTTP API        |
| `AgentRequest`      | Validates incoming requests              |
| `AgentCard`         | Describes the Flight Agent               |
| `MCP Client`        | Connects the agent to the MCP Gateway    |
| `search_flights`    | Retrieves flight data                    |
| `Flight`            | Represents structured flight information |
| `LLM`               | Recommends a flight from supplied data   |
| `FlightAgentResult` | Defines the structured agent response    |
| `MCP_GATEWAY_URL`   | Specifies the MCP Gateway location       |
| `get_llm()`         | Creates the configured LLM               |

---

# Key Design Principle

 The Flight Agent separates **tool execution** from **LLM reasoning**.

### MCP handles data retrieval

```
search_flights
      |
      v
Actual flight data
```

### LLM handles recommendation

```
Flight data
      |
      v
LLM
      |
      v
Recommendation
```

### FastAPI handles orchestration

```
HTTP request
      |
      v
Destination
      |
      v
MCP
      |
      v
Flight models
      |
      v
LLM
      |
      v
Final response
```

 This keeps the responsibilities of each component separate.

---

# Current Implementation Limitation

 Destination detection is currently hard-coded:

```
destination = "goa"

if "mumbai" in message:
    destination = "mumbai"
```

 As a result, the current implementation effectively supports:

```
Mumbai → mumbai
Everything else → goa
```

 For example:

```
"Find a flight to Mumbai"
        ↓
mumbai
```

 while:

```
"Find a flight to Delhi"
        ↓
goa
```

 A future implementation could replace this logic with dynamic destination extraction so that arbitrary destinations can be passed to:

```
search_flights
```

---

# Summary

 The Flight Agent follows this pattern:

```
HTTP Request
     ↓
FastAPI
     ↓
AgentRequest
     ↓
Determine Destination
     ↓
MCP Client
     ↓
MCP Gateway
     ↓
search_flights
     ↓
Flight Data
     ↓
Flight Models
     ↓
Check Results
     ↓
Structured LLM
     ↓
Flight Recommendation
     ↓
FlightAgentResult
     ↓
HTTP JSON Response
```

 **MCP retrieves the flight data, the LLM recommends a flight, and the Flight Agent orchestrates the complete flow.**
