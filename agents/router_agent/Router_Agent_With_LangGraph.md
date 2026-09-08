# Travel Router Agent

## Overview

 The **Travel Router Agent** is the main orchestration agent in the travel planning system.

 It is built with **FastAPI** and **LangGraph** and coordinates the Flight Agent and Hotel Agent through HTTP calls.

 The Router Agent does not directly access flight or hotel MCP tools. Instead, it:

1. Receives a user's travel request.
2. Uses an LLM to determine the destination.
3. Determines whether a flight is needed.
4. Determines whether a hotel is needed.
5. Calls the required Flight Agent and Hotel Agent.
6. Calls both agents concurrently when both are required.
7. Collects their results.
8. Selects a flight and hotel for the final plan.
9. Calculates the estimated trip cost.
10. Builds a `TravelPlan`.
11. Returns the complete result to the client.

 The implementation is located at:

```
agents/router_agent/main.py
```

---

## Architecture

 The Travel Router is the top-level agent in the travel system.

```
                         USER / CLIENT
                               |
                               | POST /
                               v
                  +-------------------------+
                  |   Travel Router Agent   |
                  |        FastAPI          |
                  +------------+------------+
                               |
                               v
                       route_request
                               |
                               | LLM
                               v
                     RouterDecision
                               |
                               v
                         call_agents
                        /           \
                       /             \
                      v               v
              Flight Agent      Hotel Agent
                   |                  |
                  HTTP               HTTP
                   |                  |
                   v                  v
              Flight Result      Hotel Result
                       \             /
                        \           /
                         +---------+
                              |
                              v
                         build_plan
                              |
                              v
                         TravelPlan
                              |
                              v
                            USER
```

 The important distinction is that the Router Agent delegates work to specialized agents rather than directly calling MCP tools.

```
                    Travel Router Agent
                            |
                    HTTP Agent Calls
                       /          \
                      v            v
               Flight Agent   Hotel Agent
                    |               |
                   MCP             MCP
                    |               |
                    v               v
             Flight Tools     Hotel Tools
```

---

# Main Technologies

- **FastAPI** — exposes the Router Agent HTTP API.
- **LangGraph** — defines and executes the orchestration workflow.
- **LLM** — interprets the user's travel request and produces a structured `RouterDecision`.
- **HTTPX** — communicates with the Flight Agent and Hotel Agent.
- **Pydantic models** — validate agent responses and define structured data.
- **Flight Agent** — handles flight-specific search and recommendation.
- **Hotel Agent** — handles hotel-specific search and recommendation.

---

# Application Startup

 The application is initialized with:

```
app = FastAPI(
    title="Travel Router Agent",
    version="1.0.0",
)

llm = get_llm()
```

 This creates the FastAPI application and initializes the LLM.

 The LLM is used by the `route_request` node to understand the user's request.

---

# TravelState

 LangGraph uses `TravelState` as the shared state between workflow nodes.

```
class TravelState(TypedDict, total=False):

    message: str

    router_decision: RouterDecision

    flight_result: FlightAgentResult | None

    hotel_result: HotelAgentResult | None

    travel_plan: TravelPlan
```

 The state contains:

| Field               | Purpose                             |
| ------------------- | ----------------------------------- |
| `message`         | Original user request               |
| `router_decision` | LLM-generated routing decision      |
| `flight_result`   | Result returned by the Flight Agent |
| `hotel_result`    | Result returned by the Hotel Agent  |
| `travel_plan`     | Final combined travel plan          |

 The state gradually becomes:

```
Initial State
    |
    +-- message
    |
    v
After route_request
    |
    +-- message
    +-- router_decision
    |
    v
After call_agents
    |
    +-- message
    +-- router_decision
    +-- flight_result
    +-- hotel_result
    |
    v
After build_plan
    |
    +-- message
    +-- router_decision
    +-- flight_result
    +-- hotel_result
    +-- travel_plan
```

---

# LangGraph Workflow

 The actual graph contains **three nodes**:

```
START
  |
  v
route_request
  |
  v
call_agents
  |
  v
build_plan
  |
  v
END
```

 The graph is created with:

```
builder = StateGraph(
    TravelState
)

builder.add_node(
    "route_request",
    route_request,
)

builder.add_node(
    "call_agents",
    call_agents,
)

builder.add_node(
    "build_plan",
    build_plan,
)
```

 The edges are:

```
builder.add_edge(
    START,
    "route_request",
)

builder.add_edge(
    "route_request",
    "call_agents",
)

builder.add_edge(
    "call_agents",
    "build_plan",
)

builder.add_edge(
    "build_plan",
    END,
)
```

 Therefore, the actual LangGraph execution is:

```
START
  |
  v
route_request
  |
  v
call_agents
  |
  v
build_plan
  |
  v
END
```

### Important

 The Flight Agent and Hotel Agent are **not separate LangGraph nodes in the current implementation**.

 Instead, both are called from the single:

```
call_agents()
```

 node.

---

# Step 1: Receive User Request

 The Router exposes:

```
POST /
```

 The endpoint is:

```
@app.post("/")
async def travel(
    request: AgentRequest,
):
```

 For example, the client can send:

```
{
  "message": "Plan a 3 day trip to Goa. Find me a flight and hotel."
}
```

 FastAPI validates the request using:

```
AgentRequest
```

 The user's message is then passed into LangGraph:

```
result = await travel_graph.ainvoke(
    {
        "message": request.message
    }
)
```

 The initial state is therefore:

```
{
    "message": "Plan a 3 day trip to Goa. Find me a flight and hotel."
}
```

---

# Step 2: Route the Request

 The first node is:

```
def route_request(
    state: TravelState,
):
```

 This node is responsible for understanding what the user needs.

 It creates a structured LLM:

```
structured_llm = llm.with_structured_output(
    RouterDecision
)
```

 The LLM is instructed to determine:

- destination
- whether a flight is needed
- whether a hotel is needed

 For example:

```
Plan a 3 day trip to Goa.
Find me a flight and hotel.
```

 The expected structured decision is approximately:

```
{
  "destination": "Goa",
  "needs_flight": true,
  "needs_hotel": true
}
```

 The result is a `RouterDecision` object.

 The node returns:

```
return {
    "router_decision": decision
}
```

 The state now contains:

```
message
   |
   v
router_decision
   |
   +-- destination = Goa
   +-- needs_flight = true
   +-- needs_hotel = true
```

---

# RouterDecision

 The Router does not hard-code the destination or requirements.

 Instead, the LLM determines them from the user's message.

 For example:

### Flight and hotel requested

```
"Plan a trip to Goa with a flight and hotel."
```

 Could produce:

```
destination = Goa
needs_flight = true
needs_hotel = true
```

### Only hotel requested

```
"Find me a hotel in Goa."
```

 Could produce:

```
destination = Goa
needs_flight = false
needs_hotel = true
```

### Only flight requested

```
"Find me a flight to Goa."
```

 Could produce:

```
destination = Goa
needs_flight = true
needs_hotel = false
```

 The Router therefore decides which specialized agents need to be called.

---

# Step 3: Call Agents

 After routing, LangGraph moves to:

```
async def call_agents(
    state: TravelState,
):
```

 This function retrieves:

```
decision = state["router_decision"]
```

 It then creates a list of asynchronous tasks.

---

# Flight Agent Delegation

 If:

```
decision.needs_flight
```

 is `True`, the Router adds:

```
call_flight_agent(
    state["message"]
)
```

 to the task list.

 If a flight is not required, it adds:

```
asyncio.sleep(
    0,
    result=None,
)
```

 This ensures the final result still has the expected position for the flight result.

---

# Hotel Agent Delegation

 The same logic is applied to hotels.

 If:

```
decision.needs_hotel
```

 is `True`, the Router adds:

```
call_hotel_agent(
    state["message"]
)
```

 Otherwise it adds:

```
asyncio.sleep(
    0,
    result=None,
)
```

---

# Parallel Agent Execution

 The most important part of `call_agents()` is:

```
flight_result, hotel_result = (
    await asyncio.gather(*tasks)
)
```

 This means that when both agents are required, the Router executes their HTTP calls concurrently.

 Conceptually:

```
                    call_agents
                         |
              +----------+----------+
              |                     |
              v                     v
       call_flight_agent      call_hotel_agent
              |                     |
              | HTTP                | HTTP
              v                     v
        Flight Agent          Hotel Agent
              |                     |
              +----------+----------+
                         |
                         v
                  asyncio.gather()
```

 This is more accurate than describing Flight and Hotel as separate LangGraph nodes.

 They are **parallel asynchronous agent calls inside the `call_agents` LangGraph node**.

---

# Step 4: Call Flight Agent

 The Router communicates with the Flight Agent using HTTPX.

 The function is:

```
async def call_flight_agent(
    message: str,
):
```

 It creates an asynchronous HTTP client:

```
async with httpx.AsyncClient(
    timeout=60
) as client:
```

 Then sends:

```
response = await client.post(
    f"{FLIGHT_AGENT_URL}/",
    json={
        "message": message
    },
)
```

 The Flight Agent URL comes from:

```
FLIGHT_AGENT_URL
```

 which is imported from:

```
common.config
```

 The communication flow is:

```
Travel Router
      |
      | HTTP POST
      v
FLIGHT_AGENT_URL
      |
      v
Flight Agent
      |
      v
FlightAgentResult
      |
      v
Travel Router
```

---

# Flight Response Validation

 After the Flight Agent responds:

```
response.raise_for_status()
```

 checks whether the HTTP request was successful.

 Then:

```
return FlightAgentResult.model_validate(
    response.json()
)
```

 converts the JSON response into a validated:

```
FlightAgentResult
```

 The Router therefore does not blindly trust arbitrary JSON.

 The response is validated against the expected Pydantic model.

---

# Step 5: Call Hotel Agent

 The Hotel Agent is called using:

```
async def call_hotel_agent(
    message: str,
):
```

 The Router sends:

```
response = await client.post(
    f"{HOTEL_AGENT_URL}/",
    json={
        "message": message
    },
)
```

 The Hotel Agent URL comes from:

```
HOTEL_AGENT_URL
```

 The flow is:

```
Travel Router
      |
      | HTTP POST
      v
HOTEL_AGENT_URL
      |
      v
Hotel Agent
      |
      v
HotelAgentResult
      |
      v
Travel Router
```

 The response is validated with:

```
return HotelAgentResult.model_validate(
    response.json()
)
```

---

# Agent-to-Agent Communication

 The Router uses HTTP to communicate with the specialized agents.

```
                 Travel Router
                       |
             +---------+---------+
             |                   |
             | HTTP              | HTTP
             v                   v
       Flight Agent         Hotel Agent
             |                   |
             | MCP               | MCP
             v                   v
       Flight Tools         Hotel Tools
```

 This creates a layered architecture:

```
User
 |
 | HTTP
 v
Travel Router Agent
 |
 | HTTP
 +--------------------+
 |                    |
 v                    v
Flight Agent       Hotel Agent
 |                    |
 | MCP                | MCP
 v                    v
Flight Tools        Hotel Tools
```

 The Router itself does **not** call `search_flights` or `search_hotels`.

 The specialized agents are responsible for accessing those tools.

---

# Step 6: Store Agent Results

 After both asynchronous calls complete:

```
flight_result, hotel_result = (
    await asyncio.gather(*tasks)
)
```

 the node returns:

```
return {
    "flight_result": flight_result,
    "hotel_result": hotel_result,
}
```

 The LangGraph state now contains:

```
router_decision
       |
       +-- destination
       +-- needs_flight
       +-- needs_hotel

flight_result
       |
       +-- flights
       +-- recommendation

hotel_result
       |
       +-- hotels
       +-- recommendation
```

---

# Step 7: Build the Travel Plan

 The next LangGraph node is:

```
def build_plan(
    state: TravelState,
):
```

 It retrieves:

```
decision = state["router_decision"]

flight_result = state.get(
    "flight_result"
)

hotel_result = state.get(
    "hotel_result"
)
```

 It then initializes:

```
selected_flight = None
selected_hotel = None

flight_cost = 0.0
hotel_cost = 0.0

duration_days = 3
```

---

# Step 8: Select Flight

 If flight results are available:

```
if (
    flight_result
    and flight_result.flights
):
```

 the Router selects:

```
selected_flight = min(
    flight_result.flights,
    key=lambda flight: flight.price,
)
```

 This means the Router selects the **cheapest flight**.

 For example:

```
IndiGo      ₹4,500
Air India   ₹6,000
Vistara     ₹5,200
```

 The selected flight is:

```
IndiGo → ₹4,500
```

 The flight cost is then:

```
flight_cost = selected_flight.price
```

### Important

 The final Router selection is based on **price**, regardless of the recommendation text returned by the Flight Agent.

---

# Step 9: Select Hotel

 If hotel results are available:

```
if (
    hotel_result
    and hotel_result.hotels
):
```

 the Router selects:

```
selected_hotel = max(
    hotel_result.hotels,
    key=lambda hotel: hotel.rating,
)
```

 This means the Router selects the **highest-rated hotel**.

 For example:

```
Hotel A → 4.2
Hotel B → 4.8
Hotel C → 4.5
```

 The selected hotel is:

```
Hotel B → 4.8
```

### Important

 The final Router selection is based on **rating**, regardless of the recommendation text returned by the Hotel Agent.

---

# Step 10: Calculate Hotel Cost

 The hotel cost is calculated using:

```
hotel_cost = (
    selected_hotel.price_per_night
    * selected_hotel.nights
)
```

 For example:

```
Price per night = ₹4,000
Nights          = 2
```

 Therefore:

```
₹4,000 × 2 = ₹8,000
```

 The estimated hotel cost is:

```
₹8,000
```

---

# Step 11: Calculate Total Cost

 The total cost is:

```
total = (
    flight_cost
    + hotel_cost
)
```

 For example:

```
Flight = ₹4,500
Hotel  = ₹8,000
----------------
Total  = ₹12,500
```

---

# Step 12: Build Summary

 The Router creates a summary starting with:

```
summary = (
    f"Recommended trip to "
    f"{decision.destination}. "
)
```

 If a flight is selected, it adds:

```
summary += (
    f"Flight: "
    f"{selected_flight.airline} "
    f"{selected_flight.flight}. "
)
```

 For example:

```
Flight: IndiGo 6E123.
```

 If a hotel is selected, it adds:

```
summary += (
    f"Hotel: "
    f"{selected_hotel.name}. "
)
```

 For example:

```
Hotel: Goa Resort.
```

 Finally:

```
summary += (
    f"Estimated total cost: "
    f"₹{total:.2f}."
)
```

 The final summary could therefore be:

```
Recommended trip to Goa. Flight: IndiGo 6E123. Hotel: Goa Resort. Estimated total cost: ₹12500.00.
```

---

# Step 13: Create TravelPlan

 The Router creates the final structured plan:

```
TravelPlan(
    destination=decision.destination,
    duration_days=duration_days,
    selected_flight=selected_flight,
    selected_hotel=selected_hotel,
    estimated_flight_cost=flight_cost,
    estimated_hotel_cost=hotel_cost,
    estimated_total_cost=total,
    summary=summary,
)
```

 The `TravelPlan` contains:

```
TravelPlan
 |
 +-- destination
 +-- duration_days
 +-- selected_flight
 +-- selected_hotel
 +-- estimated_flight_cost
 +-- estimated_hotel_cost
 +-- estimated_total_cost
 +-- summary
```

 The node returns:

```
return {
    "travel_plan": TravelPlan(...)
}
```

---

# Step 14: LangGraph Completes

 The final graph edge is:

```
builder.add_edge(
    "build_plan",
    END,
)
```

 Therefore:

```
START
  |
  v
route_request
  |
  v
call_agents
  |
  v
build_plan
  |
  v
END
```

 After `ainvoke()` completes, the Router has access to the complete state.

---

# Step 15: Return API Response

 The API retrieves:

```
decision = result[
    "router_decision"
]
```

 and:

```
flight_result = result.get(
    "flight_result"
)

hotel_result = result.get(
    "hotel_result"
)
```

 The final response is:

```
return {
    "agent": "travel-router-agent",

    "destination": (
        decision.destination
    ),

    "decision": (
        decision.model_dump()
    ),

    "flight_agent": (
        flight_result.model_dump()
        if flight_result
        else None
    ),

    "hotel_agent": (
        hotel_result.model_dump()
        if hotel_result
        else None
    ),

    "travel_plan": (
        result["travel_plan"]
        .model_dump()
    ),
}
```

 This exposes both the intermediate agent results and the final travel plan.

---

# API Endpoints

## Health Check

```
GET /
```

 The health endpoint returns:

```
{
  "status": "ok",
  "agent": "travel-router-agent",
  "orchestration": "langgraph"
}
```

 This endpoint is useful for checking whether the Router Agent is running.

---

# Travel Planning API

```
POST /
```

 Request:

```
{
  "message": "Plan a 3 day trip to Goa. Find me a flight and hotel."
}
```

 The request is processed by the LangGraph workflow.

```
POST /
  |
  v
route_request
  |
  v
call_agents
  |
  +----> Flight Agent
  |
  +----> Hotel Agent
  |
  v
build_plan
  |
  v
TravelPlan
```

---

# Example End-to-End Request

 Input:

```
{
  "message": "Plan a 3 day trip to Goa. Find me a flight and hotel."
}
```

## Router Decision

 The LLM may produce:

```
{
  "destination": "Goa",
  "needs_flight": true,
  "needs_hotel": true
}
```

 The Router then calls both agents.

---

# Flight Agent Result

 The Flight Agent might return:

```
{
  "destination": "goa",
  "flights": [
    {
      "airline": "IndiGo",
      "flight": "6E123",
      "price": 4500
    },
    {
      "airline": "Air India",
      "flight": "AI456",
      "price": 6000
    }
  ],
  "recommendation": "IndiGo is a good option."
}
```

 The Router selects:

```
IndiGo 6E123
₹4,500
```

 because it has the lowest price.

---

# Hotel Agent Result

 The Hotel Agent might return:

```
{
  "destination": "goa",
  "hotels": [
    {
      "name": "Goa Resort",
      "price_per_night": 4000,
      "rating": 4.5,
      "nights": 2
    },
    {
      "name": "Beach Hotel",
      "price_per_night": 3500,
      "rating": 4.2,
      "nights": 2
    }
  ],
  "recommendation": "Goa Resort has the highest rating."
}
```

 The Router selects:

```
Goa Resort
Rating: 4.5
```

 because it has the highest rating.

 The hotel cost is:

```
₹4,000 × 2
= ₹8,000
```

---

# Final Cost

 The Router calculates:

```
Flight
₹4,500

Hotel
₹8,000

----------------
Total
₹12,500
```

---

# Example Final Response

 The API response can look like:

```
{
  "agent": "travel-router-agent",

  "destination": "Goa",

  "decision": {
    "destination": "Goa",
    "needs_flight": true,
    "needs_hotel": true
  },

  "flight_agent": {
    "destination": "goa",
    "flights": [
      {
        "airline": "IndiGo",
        "flight": "6E123",
        "price": 4500
      },
      {
        "airline": "Air India",
        "flight": "AI456",
        "price": 6000
      }
    ],
    "recommendation": "IndiGo is a good option."
  },

  "hotel_agent": {
    "destination": "goa",
    "hotels": [
      {
        "name": "Goa Resort",
        "price_per_night": 4000,
        "rating": 4.5,
        "nights": 2
      },
      {
        "name": "Beach Hotel",
        "price_per_night": 3500,
        "rating": 4.2,
        "nights": 2
      }
    ],
    "recommendation": "Goa Resort has the highest rating."
  },

  "travel_plan": {
    "destination": "Goa",
    "duration_days": 3,
    "selected_flight": {
      "airline": "IndiGo",
      "flight": "6E123",
      "price": 4500
    },
    "selected_hotel": {
      "name": "Goa Resort",
      "price_per_night": 4000,
      "rating": 4.5,
      "nights": 2
    },
    "estimated_flight_cost": 4500,
    "estimated_hotel_cost": 8000,
    "estimated_total_cost": 12500,
    "summary": "Recommended trip to Goa. Flight: IndiGo 6E123. Hotel: Goa Resort. Estimated total cost: ₹12500.00."
  }
}
```

---

# Complete Workflow

 The actual implementation can be summarized as:

```
                         USER
                           |
                           | POST /
                           v
                +----------------------+
                | Travel Router Agent  |
                |       FastAPI        |
                +----------+-----------+
                           |
                           v
                  +----------------+
                  | route_request  |
                  +-------+--------+
                          |
                          | LLM
                          v
                  +----------------+
                  | RouterDecision |
                  +-------+--------+
                          |
                          v
                  +----------------+
                  |  call_agents   |
                  +-------+--------+
                          |
                 +--------+--------+
                 |                 |
                 | asyncio.gather  |
                 |                 |
                 v                 v
        +----------------+ +----------------+
        | Flight Agent   | | Hotel Agent    |
        +-------+--------+ +-------+--------+
                |                  |
                | HTTP             | HTTP
                v                  v
        FlightAgentResult   HotelAgentResult
                |                  |
                +--------+---------+
                         |
                         v
                  +--------------+
                  |  build_plan  |
                  +------+-------+
                         |
              +----------+----------+
              |                     |
              v                     v
        Cheapest Flight      Highest-rated Hotel
              |                     |
              +----------+----------+
                         |
                         v
                  Calculate Cost
                         |
                         v
                   TravelPlan
                         |
                         v
                        END
                         |
                         v
                       USER
```

---

# Router Agent vs Specialized Agents

 The system contains three agents with different responsibilities.

## Travel Router Agent

 The Router is responsible for orchestration:

```
Understand request
       |
       v
Create RouterDecision
       |
       v
Delegate to agents
       |
       v
Collect results
       |
       v
Build TravelPlan
```

## Flight Agent

 The Flight Agent handles flight-specific operations:

```
Receive request
       |
       v
Search flights
       |
       v
Evaluate flights
       |
       v
Return FlightAgentResult
```

## Hotel Agent

 The Hotel Agent handles hotel-specific operations:

```
Receive request
       |
       v
Search hotels
       |
       v
Evaluate hotels
       |
       v
Return HotelAgentResult
```

 The architecture therefore follows:

```
                 Travel Router
                      |
              Agent-to-Agent HTTP
                 /            \
                v              v
         Flight Agent      Hotel Agent
                |              |
               MCP            MCP
                |              |
                v              v
        Flight Search      Hotel Search
```

---

# HTTP vs MCP Responsibilities

 There are two distinct communication layers.

## Router → Specialized Agents

 The Router uses HTTP:

```
Travel Router
      |
      | HTTPX
      v
Flight Agent
```

 and:

```
Travel Router
      |
      | HTTPX
      v
Hotel Agent
```

## Specialized Agents → Tools

 The specialized agents use MCP:

```
Flight Agent
     |
     | MCP
     v
MCP Gateway
     |
     v
search_flights
```

 and:

```
Hotel Agent
     |
     | MCP
     v
MCP Gateway
     |
     v
search_hotels
```

 Therefore:

```
USER
 |
 | HTTP
 v
TRAVEL ROUTER
 |
 +---- HTTP ----> FLIGHT AGENT ---- MCP ----> Flight Tool
 |
 +---- HTTP ----> HOTEL AGENT  ---- MCP ----> Hotel Tool
 |
 v
TRAVEL PLAN
```

---

# Current Selection Logic

 The Router's final selection logic is deterministic.

## Flight

 The cheapest flight is selected:

```
min(
    flight_result.flights,
    key=lambda flight: flight.price,
)
```

 Therefore:

```
Lowest price → Selected flight
```

## Hotel

 The highest-rated hotel is selected:

```
max(
    hotel_result.hotels,
    key=lambda hotel: hotel.rating,
)
```

 Therefore:

```
Highest rating → Selected hotel
```

 The Router does not use the textual `recommendation` returned by either specialized agent when selecting the final flight or hotel.

---

# Current Limitations

 There are several hard-coded or implementation-specific behaviors in the current version.

## 1\. Trip duration is hard-coded

 The code contains:

```
duration_days = 3
```

 Therefore every `TravelPlan` currently reports:

```
duration_days = 3
```

 regardless of the duration requested by the user.

 A future version could add duration to `RouterDecision` and use it here.

---

## 2\. Flight selection only considers price

 The Router selects:

```
min(
    flight_result.flights,
    key=lambda flight: flight.price,
)
```

 Therefore the final flight is always the cheapest available flight.

 The Flight Agent's recommendation does not affect this final selection.

---

## 3\. Hotel selection only considers rating

 The Router selects:

```
max(
    hotel_result.hotels,
    key=lambda hotel: hotel.rating,
)
```

 Therefore the final hotel is always the highest-rated available hotel.

 Price is used only when calculating the final hotel cost.

---

## 4\. Agent calls depend on the Router LLM

 The Router uses:

```
llm.with_structured_output(
    RouterDecision
)
```

 to determine whether the Flight Agent and Hotel Agent should be called.

 Therefore the quality of routing depends on the LLM correctly interpreting the user's request.

---

## 5\. Both agents receive the original user message

 The Router passes:

```
state["message"]
```

 to both specialized agents.

 For example:

```
"Plan a 3 day trip to Goa. Find me a flight and hotel."
```

 is sent unchanged to both the Flight Agent and Hotel Agent.

 The Router does not currently create separate specialized instructions such as:

```
"Find flights to Goa"
```

 and:

```
"Find hotels in Goa for 2 nights"
```

---

# Why LangGraph Is Used

 LangGraph provides a structured workflow around the Router Agent.

 Instead of manually writing:

```
call router
call flight
call hotel
build result
```

 the workflow is represented as a graph:

```
START
  |
  v
route_request
  |
  v
call_agents
  |
  v
build_plan
  |
  v
END
```

 The graph state carries information between each stage.

 This makes the orchestration easier to extend later.

 For example, future nodes could include:

```
route_request
      |
      v
validate_request
      |
      v
call_agents
      |
      v
check_budget
      |
      v
build_plan
      |
      v
END
```

---

# Complete System Architecture

 The complete travel system is:

```
                                USER
                                  |
                                  | HTTP
                                  v
                    +-------------------------+
                    |   Travel Router Agent   |
                    |                         |
                    |        FastAPI          |
                    |        LangGraph        |
                    +------------+------------+
                                 |
                                 | LLM
                                 v
                         RouterDecision
                                 |
                                 v
                           call_agents
                          /           \
                         /             \
                        v               v
              +----------------+ +----------------+
              |  Flight Agent  | |  Hotel Agent   |
              +-------+--------+ +-------+--------+
                      |                  |
                      | MCP              | MCP
                      v                  v
              +---------------+  +---------------+
              | Flight Tools  |  | Hotel Tools   |
              +---------------+  +---------------+
                      |                  |
                      v                  v
                Flight Results      Hotel Results
                      |                  |
                      +--------+---------+
                               |
                               v
                         build_plan
                               |
                     +---------+---------+
                     |                   |
                     v                   v
                Cheapest Flight    Highest-rated
                                      Hotel
                     |                   |
                     +---------+---------+
                               |
                               v
                         Cost Calculation
                               |
                               v
                          TravelPlan
                               |
                               v
                              USER
```

---

# Summary

 The **Travel Router Agent** is the orchestration layer of the travel planning system.

 Its actual implementation is:

```
User Request
     |
     v
FastAPI
     |
     v
LangGraph
     |
     v
route_request
     |
     | LLM
     v
RouterDecision
     |
     v
call_agents
     |
     +------ asyncio.gather() ------+
     |                              |
     v                              v
Flight Agent                   Hotel Agent
     |                              |
     | HTTP                         | HTTP
     v                              v
FlightAgentResult             HotelAgentResult
     |                              |
     +--------------+---------------+
                    |
                    v
               build_plan
                    |
                    v
            Cheapest Flight
                    +
            Highest-rated Hotel
                    |
                    v
            Calculate Total Cost
                    |
                    v
               TravelPlan
                    |
                    v
                   END
```

 The key architectural principle is:

> **The Travel Router Agent is responsible for orchestration, while the Flight Agent and Hotel Agent are responsible for their respective domains. The Router uses an LLM for routing decisions, HTTP for agent-to-agent communication, LangGraph for workflow orchestration, and the specialized agents use MCP to access their tools.**

 In short:

```
Router Agent
    |
    +--> decides what is needed
    |
    +--> delegates to Flight Agent
    |
    +--> delegates to Hotel Agent
    |
    +--> collects results
    |
    +--> selects final options
    |
    +--> calculates cost
    |
    +--> returns TravelPlan
```
