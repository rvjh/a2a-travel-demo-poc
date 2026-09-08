 # Travel Router Agent

 ## Overview

Router Agent with LangGraph

This is the most important part.

The Router Agent is itself an agent.

It has a LangGraph workflow:

START
  |
  v
route_request
  |
  +----------+
  |          |
  v          v
flight     hotel
  |          |
  +----+-----+
       |
       v
  build_plan
       |
       v
      END


The router does not directly access the MCP tools.

Instead

Router
  |
  +--> Flight Agent
  |
  +--> Hotel Agent


This gives us genuine agent-to-agent delegation

agents/router_agent/main.py


 The **Travel Router Agent** is the main orchestrator in the travel planning system.

 Unlike the Flight Agent and Hotel Agent, this agent does not directly search for flights or hotels.

 Instead, it:

 1. Receives the user's travel request.
2. Uses an LLM to understand what the user needs.
3. Decides whether a flight and/or hotel is required.
4. Calls the Flight Agent and Hotel Agent through HTTP/A2A-style communication.
5. Collects their results.
6. Selects a flight and hotel.
7. Calculates the estimated total cost.
8. Builds a final `TravelPlan`.
9. Returns the complete travel plan to the client.

 The overall architecture is:

```
                         USER
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
                 +---------+---------+
                 |                   |
                 v                   v
           Flight Node          Hotel Node
                 |                   |
                 | HTTP              | HTTP
                 v                   v
          Flight Agent          Hotel Agent
                 |                   |
                 |                   |
                 v                   v
          Flight Results        Hotel Results
                 |                   |
                 +---------+---------+
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

---

 # Architecture

 The Travel Router sits above the Flight and Hotel Agents.

```
                         +----------------+
                         |      User      |
                         +-------+--------+
                                 |
                                 | Travel request
                                 v
                    +-------------------------+
                    |   Travel Router Agent   |
                    |                         |
                    |       FastAPI           |
                    +------------+------------+
                                 |
                                 v
                       +----------------+
                       |   LLM Router   |
                       |                |
                       |  destination   |
                       |  flight?       |
                       |  hotel?        |
                       +-------+--------+
                               |
                    +----------+----------+
                    |                     |
                    v                     v
             +-------------+       +-------------+
             | Flight Node |       | Hotel Node  |
             +------+------+       +------+------+
                    |                     |
                    | HTTP                | HTTP
                    v                     v
             +-------------+       +-------------+
             | Flight      |       | Hotel       |
             | Agent       |       | Agent       |
             +------+------+       +------+------+
                    |                     |
                    v                     v
             Flight Result          Hotel Result
                    |                     |
                    +----------+----------+
                               |
                               v
                      +----------------+
                      |  Build Plan    |
                      |                |
                      | Select flight  |
                      | Select hotel   |
                      | Calculate cost |
                      +-------+--------+
                              |
                              v
                       TravelPlan
                              |
                              v
                             User
```

---

 # Main Technologies

 The application uses:

 - **FastAPI** — exposes the Travel Router HTTP API.
- **LangGraph** — controls the agent workflow.
- **LLM** — determines what the user needs.
- **HTTPX** — communicates with Flight and Hotel Agents.
- **Pydantic** — validates structured data.
- **Flight Agent** — searches/recommends flights.
- **Hotel Agent** — searches/recommends hotels.

---

 # Application Startup

 The application starts with:

```
app = FastAPI(title="Travel Router Agent")

llm = get_llm()
```

 The first line creates the FastAPI application.

 The second line initializes the LLM:

```
llm = get_llm()
```

 The LLM is later used by the router to understand the user's request.

 The application therefore has:

```
FastAPI
   |
   +── POST /
   |
   +── LangGraph
          |
          +── Router
          +── Flight Agent
          +── Hotel Agent
          +── Build Plan
```

---

 # LangGraph State

 The central state of the workflow is:

```
class TravelState(TypedDict, total=False):
    message: str
    router_decision: RouterDecision
    flight_result: FlightAgentResult | None
    hotel_result: HotelAgentResult | None
    travel_plan: TravelPlan
```

 This state is shared between the different LangGraph nodes.

 Think of it as a shared object moving through the graph.

 Initially:

```
TravelState
    |
    +── message
```

 After routing:

```
TravelState
    |
    +── message
    +── router_decision
```

 After Flight Agent:

```
TravelState
    |
    +── message
    +── router_decision
    +── flight_result
```

 After Hotel Agent:

```
TravelState
    |
    +── message
    +── router_decision
    +── flight_result
    +── hotel_result
```

 Finally:

```
TravelState
    |
    +── message
    +── router_decision
    +── flight_result
    +── hotel_result
    +── travel_plan
```

---

 # LangGraph Nodes

 There are four nodes in the graph:

```
route_request
      |
      +---- flight_agent
      |
      +---- hotel_agent
              |
              v
          build_plan
```

 The nodes are:

 | Node | Responsibility |
| --- | --- |
| `route_request` | Understand the user request |
| `flight_agent` | Call Flight Agent if required |
| `hotel_agent` | Call Hotel Agent if required |
| `build_plan` | Select options and build final plan |

---

 # Step 1: User Sends Request

 The API endpoint is:

```
POST /
```

 The endpoint is:

```
@app.post("/")
async def travel(request: AgentRequest):
```

 A user might send:

```
{
  "message": "Plan a 3 day trip to Goa. Find a flight and hotel."
}
```

 FastAPI converts this into:

```
AgentRequest
```

 and passes it to:

```
travel()
```

---

 # Step 2: Start the LangGraph

 Inside the API function:

```
result = await travel_graph.ainvoke(
    {
        "message": request.message
    }
)
```

 The graph starts with:

```
message
   |
   v
START
   |
   v
route_request
```

 Initially the graph state is:

```
{
    "message": "Plan a 3 day trip to Goa. Find a flight and hotel."
}
```

---

 # Step 3: Router Node

 The first LangGraph node is:

```
def route_request(state: TravelState):
```

 This node determines what the user wants.

 It creates a structured LLM:

```
structured_llm = llm.with_structured_output(
    RouterDecision
)
```

 This means the LLM must return a structure matching:

```
RouterDecision
```

 The LLM is given the user's request.

 For example:

```
You are the Router Agent for a travel planning system.

User request:
Plan a 3 day trip to Goa. Find a flight and hotel.

Determine:

1. destination
2. whether a flight is required
3. whether a hotel is required
```

---

 # Step 4: LLM Creates Router Decision

 The LLM analyzes the request.

 For:

```
Plan a 3 day trip to Goa. Find a flight and hotel.
```

 the expected result is approximately:

```
{
  "destination": "Goa",
  "needs_flight": true,
  "needs_hotel": true
}
```

 This becomes a:

```
RouterDecision
```

 object.

 The node returns:

```
return {
    "router_decision": decision
}
```

 The state now becomes:

```
TravelState
   |
   +── message
   |
   +── router_decision
          |
          +── destination = Goa
          +── needs_flight = true
          +── needs_hotel = true
```

---

 # Step 5: LangGraph Moves to Flight and Hotel Nodes

 The graph is constructed with:

```
builder.add_edge(START, "route_request")

builder.add_edge(
    "route_request",
    "flight_agent"
)

builder.add_edge(
    "route_request",
    "hotel_agent"
)
```

 This is important.

 After `route_request`, there are **two outgoing paths**:

```
                 route_request
                  /          \
                 /            \
                v              v
        flight_agent       hotel_agent
```

 So when both are required, the Flight Agent and Hotel Agent can be executed independently.

 Conceptually:

```
                 Router
                   |
          +--------+--------+
          |                 |
          v                 v
       Flight             Hotel
       Agent              Agent
          |                 |
          +--------+--------+
                   |
                   v
               Build Plan
```

---

 # Step 6: Flight Node

 The Flight node is:

```
async def flight_node(state: TravelState):
```

 It gets the router decision:

```
decision = state["router_decision"]
```

 Then checks:

```
if not decision.needs_flight:
    return {"flight_result": None}
```

 So there are two possibilities.

 ### Flight not required

 For:

```
Find me a hotel in Goa
```

 the router may return:

```
needs_flight = false
needs_hotel = true
```

 Then the Flight node returns:

```
{
    "flight_result": None
}
```

 No Flight Agent call is made.

 ### Flight required

 For:

```
Find me a flight to Goa
```

 the router may return:

```
needs_flight = true
```

 Then:

```
result = await call_flight_agent(
    state["message"]
)
```

 is executed.

---

 # Step 7: Call Flight Agent

 The function:

```
async def call_flight_agent(
    message: str
) -> FlightAgentResult:
```

 creates an HTTP client:

```
async with httpx.AsyncClient(timeout=30) as client:
```

 Then it sends:

```
response = await client.post(
    f"{FLIGHT_AGENT_URL}/",
    json={
        "message": message
    }
)
```

 So the Travel Router calls the Flight Agent through HTTP.

 The flow is:

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
MCP search_flights
      |
      v
Flight Result
      |
      v
Travel Router
```

 This is the **agent-to-agent communication** part of the architecture.

---

 # Step 8: Validate Flight Response

 After receiving the HTTP response:

```
response.raise_for_status()
```

 checks whether the request was successful.

 If the Flight Agent returns an error such as HTTP 500, an exception is raised.

 If successful:

```
return FlightAgentResult.model_validate(
    response.json()
)
```

 converts the JSON response into:

```
FlightAgentResult
```

 So:

```
Flight Agent JSON
       |
       v
response.json()
       |
       v
FlightAgentResult.model_validate()
       |
       v
FlightAgentResult object
```

 The Flight result is then stored in the graph state:

```
{
    "flight_result": result
}
```

---

 # Step 9: Hotel Node

 The Hotel node works almost exactly the same way.

```
async def hotel_node(state: TravelState):
```

 It first gets:

```
decision = state["router_decision"]
```

 Then:

```
if not decision.needs_hotel:
    return {
        "hotel_result": None
    }
```

 If a hotel isn't required, the Hotel Agent isn't called.

 If a hotel is required:

```
result = await call_hotel_agent(
    state["message"]
)
```

 is executed.

---

 # Step 10: Call Hotel Agent

 The HTTP call is:

```
response = await client.post(
    f"{HOTEL_AGENT_URL}/",
    json={
        "message": message
    }
)
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
MCP search_hotels
      |
      v
Hotel Result
      |
      v
Travel Router
```

 The response is validated with:

```
HotelAgentResult.model_validate(
    response.json()
)
```

 The result is then added to the graph state:

```
{
    "hotel_result": result
}
```

---

 # Step 11: Flight and Hotel Results Come Together

 Once the Flight and Hotel nodes have completed, the graph moves to:

```
build_plan
```

 because of:

```
builder.add_edge(
    "flight_agent",
    "build_plan"
)

builder.add_edge(
    "hotel_agent",
    "build_plan"
)
```

 Conceptually:

```
             route_request
              /         \
             v           v
       flight_agent   hotel_agent
             |           |
             |           |
             +-----+-----+
                   |
                   v
              build_plan
```

 The `build_plan()` function can access:

```
state["router_decision"]

state.get("flight_result")

state.get("hotel_result")
```

---

 # Step 12: Build the Travel Plan

 The function starts by retrieving:

```
decision = state["router_decision"]

flight_result = state.get("flight_result")

hotel_result = state.get("hotel_result")
```

 Then it initializes:

```
selected_flight = None
selected_hotel = None

flight_cost = 0.0
hotel_cost = 0.0

duration_days = 3
```

 The default trip duration is currently hard-coded to:

```
3 days
```

---

 # Step 13: Select Flight

 The code:

```
if (flight_result and flight_result.flights):

    selected_flight = min(
        flight_result.flights,
        key=lambda x: x.price
    )

    flight_cost = selected_flight.price
```

 looks at all available flights.

 It selects the flight with the **lowest price**.

 For example:

```
Flight A → ₹5000
Flight B → ₹3500
Flight C → ₹6000
```

 The code selects:

```
Flight B → ₹3500
```

 because:

```
min(..., key=lambda x: x.price)
```

 means:

 > Find the object with the smallest price.

 The flow is:

```
Flight Results
     |
     v
Compare prices
     |
     v
Lowest price
     |
     v
selected_flight
```

---

 # Step 14: Select Hotel

 The hotel selection works differently.

```
if (hotel_result and hotel_result.hotels):

    selected_hotel = max(
        hotel_result.hotels,
        key=lambda x: x.rating
    )
```

 This selects the hotel with the **highest rating**.

 For example:

```
Hotel A → Rating 4.2
Hotel B → Rating 4.8
Hotel C → Rating 4.5
```

 The selected hotel is:

```
Hotel B → Rating 4.8
```

 The flow is:

```
Hotel Results
     |
     v
Compare ratings
     |
     v
Highest rating
     |
     v
selected_hotel
```

---

 # Step 15: Calculate Hotel Cost

 The hotel cost is calculated as:

```
hotel_cost = (
    selected_hotel.price_per_night
    * selected_hotel.nights
)
```

 For example:

```
Price per night = ₹4000
Nights = 2
```

 Then:

```
₹4000 × 2 = ₹8000
```

 So:

```
hotel_cost = ₹8000
```

---

 # Step 16: Calculate Total Cost

 The total is:

```
total = flight_cost + hotel_cost
```

 For example:

```
Flight = ₹3500
Hotel  = ₹8000

Total  = ₹11500
```

 So:

```
flight_cost = 3500
hotel_cost  = 8000
total       = 11500
```

---

 # Step 17: Build Summary

 The agent creates:

```
summary_parts = []
```

 If a flight was selected:

```
summary_parts.append(
    f"Flight: "
    f"{selected_flight.airline} "
    f"{selected_flight.flight}"
)
```

 For example:

```
Flight: IndiGo 6E123
```

 If a hotel was selected:

```
summary_parts.append(
    f"Hotel: "
    f"{selected_hotel.name}"
)
```

 For example:

```
Hotel: Taj Mumbai
```

 Then the final summary becomes something like:

```
Recommended Goa trip. Flight: IndiGo 6E123 | Hotel: Taj Goa. Estimated total: ₹11500.00.
```

---

 # Step 18: Create TravelPlan

 The agent creates:

```
plan = TravelPlan(
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

 So the final plan contains:

```
TravelPlan
   |
   +── destination
   +── duration_days
   +── selected_flight
   +── selected_hotel
   +── estimated_flight_cost
   +── estimated_hotel_cost
   +── estimated_total_cost
   +── summary
```

 The node returns:

```
return {
    "travel_plan": plan
}
```

---

 # Step 19: LangGraph Ends

 The graph has:

```
builder.add_edge(
    "build_plan",
    END
)
```

 So:

```
build_plan
    |
    v
   END
```

 At this point, `travel_graph.ainvoke()` returns the complete graph state.

 Conceptually:

```
result = {
    "message": "...",
    "router_decision": ...,
    "flight_result": ...,
    "hotel_result": ...,
    "travel_plan": ...
}
```

---

 # Step 20: Build API Response

 The API gets:

```
decision = result["router_decision"]
```

 Then returns:

```
{
    "agent": "travel-router-agent",
    "destination": decision.destination,
    "decision": decision.model_dump(),
    "flight_agent": ...,
    "hotel_agent": ...,
    "travel_plan": ...
}
```

 The final response contains information from **all agents**.

---

 # Example End-to-End Request

 Suppose the user sends:

```
{
  "message": "Plan a 3 day trip to Goa. Find a flight and hotel."
}
```

 ## Router decision

 The LLM might return:

```
{
  "destination": "Goa",
  "needs_flight": true,
  "needs_hotel": true
}
```

---

 ## Flight Agent

 The Router calls:

```
POST FLIGHT_AGENT_URL/
```

 with:

```
{
  "message": "Plan a 3 day trip to Goa. Find a flight and hotel."
}
```

 The Flight Agent:

```
Receives request
     ↓
Determines Goa
     ↓
Calls MCP search_flights
     ↓
Gets flights
     ↓
LLM recommends flight
     ↓
Returns FlightAgentResult
```

 Example:

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

---

 ## Hotel Agent

 At the same time, the Router calls:

```
POST HOTEL_AGENT_URL/
```

 with the same user message.

 The Hotel Agent:

```
Receives request
     ↓
Determines Goa
     ↓
Determines nights
     ↓
Calls MCP search_hotels
     ↓
Gets hotels
     ↓
LLM recommends hotel
     ↓
Returns HotelAgentResult
```

 Example:

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

---

 # Step 21: Build Final Plan

 The Router receives both results.

 ### Flight selection

 Available:

```
IndiGo → ₹4500
Air India → ₹6000
```

 The Router selects:

```
IndiGo → ₹4500
```

 because it has the lowest price.

 ### Hotel selection

 Available:

```
Goa Resort  → 4.5
Beach Hotel → 4.2
```

 The Router selects:

```
Goa Resort → 4.5
```

 because it has the highest rating.

 ### Cost calculation

 Flight:

```
₹4500
```

 Hotel:

```
₹4000 × 2 nights
= ₹8000
```

 Total:

```
₹4500 + ₹8000
= ₹12500
```

---

 # Final Response

 The Travel Router can return something conceptually like:

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
    "summary": "Recommended Goa trip. Flight: IndiGo 6E123 | Hotel: Goa Resort. Estimated total: ₹12500.00."
  }
}
```

---

 # Complete LangGraph Flow

 The most important part of this application is the LangGraph.

```
                         START
                           |
                           v
                  +----------------+
                  | route_request  |
                  |                |
                  |      LLM       |
                  +-------+--------+
                          |
                 RouterDecision
                          |
             +------------+------------+
             |                         |
             v                         v
      +--------------+         +--------------+
      | flight_agent |         | hotel_agent  |
      +------+-------+         +------+-------+
             |                        |
             | HTTP                   | HTTP
             v                        v
      +--------------+         +--------------+
      | Flight Agent |         | Hotel Agent  |
      +------+-------+         +------+-------+
             |                        |
             | FlightResult           | HotelResult
             |                        |
             +------------+-----------+
                          |
                          v
                  +---------------+
                  |   build_plan  |
                  |               |
                  | Select Flight |
                  | Select Hotel  |
                  | Calculate Cost|
                  +-------+-------+
                          |
                          v
                         END
```

---

 # How the Three Agents Work Together

 Your overall system now has three agents:

```
                  USER
                    |
                    v
          +--------------------+
          |  Travel Router     |
          |      Agent         |
          +---------+----------+
                    |
             Understand request
                    |
          +---------+---------+
          |                   |
          v                   v
 +----------------+   +----------------+
 | Flight Agent   |   | Hotel Agent    |
 +-------+--------+   +-------+--------+
         |                    |
         v                    v
   MCP Flight Tool      MCP Hotel Tool
         |                    |
         v                    v
   Flight Results       Hotel Results
         |                    |
         +---------+----------+
                   |
                   v
             Travel Router
                   |
                   v
             Final TravelPlan
```

 The responsibility of each agent is:

 ### Travel Router Agent

```
Understand request
      ↓
Decide required agents
      ↓
Call agents
      ↓
Combine results
      ↓
Build travel plan
```

 ### Flight Agent

```
Receive travel request
      ↓
Determine destination
      ↓
Call search_flights MCP tool
      ↓
Get flights
      ↓
LLM recommendation
      ↓
Return FlightAgentResult
```

 ### Hotel Agent

```
Receive travel request
      ↓
Determine destination/nights
      ↓
Call search_hotels MCP tool
      ↓
Get hotels
      ↓
LLM recommendation
      ↓
Return HotelAgentResult
```

---

 # Important: Router vs MCP vs A2A

 There are **three communication layers** in your overall system.

 ## 1\. User → Travel Router

 This is HTTP:

```
User
  |
  | HTTP POST
  v
Travel Router
```

 ## 2\. Travel Router → Flight/Hotel Agents

 This is also HTTP, used for agent-to-agent communication:

```
Travel Router
    |
    +---- HTTP ----> Flight Agent
    |
    +---- HTTP ----> Hotel Agent
```

 ## 3\. Flight/Hotel Agents → MCP

 The specialized agents use MCP to access tools:

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

 So the overall architecture is:

```
                         USER
                           |
                           | HTTP
                           v
                  +------------------+
                  | Travel Router    |
                  |      Agent       |
                  +--------+---------+
                           |
                    HTTP / Agent calls
                    /               \
                   /                 \
                  v                   v
        +----------------+   +----------------+
        | Flight Agent   |   | Hotel Agent    |
        +-------+--------+   +-------+--------+
                |                    |
               MCP                  MCP
                |                    |
                v                    v
        +---------------+    +---------------+
        | MCP Gateway   |    | MCP Gateway   |
        +-------+-------+    +-------+-------+
                |                    |
                v                    v
        search_flights        search_hotels
```

---

 # Important Current Behavior

 There are a few things to be aware of in the current implementation.

 ## 1\. Final flight selection is based only on price

 The Flight Agent's LLM may recommend a flight using its own reasoning, but the Router ultimately does:

```
selected_flight = min(
    flight_result.flights,
    key=lambda x: x.price
)
```

 So the Router selects the **cheapest flight**.

```
Flight Agent recommendation
          |
          X
          |
Travel Router ignores recommendation
          |
          v
Select cheapest flight
```

 The final Travel Plan therefore uses the cheapest flight rather than necessarily the Flight Agent's LLM recommendation.

---

 ## 2\. Final hotel selection is based only on rating

 The Router does:

```
selected_hotel = max(
    hotel_result.hotels,
    key=lambda x: x.rating
)
```

 So it selects the hotel with the **highest rating**.

 The Hotel Agent's recommendation is not directly used to make this final selection.

```
Hotel Agent recommendation
          |
          X
          |
Travel Router
          |
          v
Select highest-rated hotel
```

---

 ## 3\. Duration is hard-coded

 Currently:

```
duration_days = 3
```

 So every final travel plan has:

```
{
  "duration_days": 3
}
```

 regardless of what the user actually requested.

 A future version should derive the duration from the `RouterDecision` or from the user request.

---

 # Final End-to-End Flow

 The entire system can be understood in one diagram:

```
                               USER
                                 |
                                 | "Plan 3 days in Goa
                                 |  with flight and hotel"
                                 v
                    +--------------------------+
                    |   TRAVEL ROUTER AGENT    |
                    |         FastAPI           |
                    +------------+-------------+
                                 |
                                 v
                       +----------------+
                       |   Router LLM   |
                       +-------+--------+
                               |
                               v
                     +-------------------+
                     | RouterDecision    |
                     |                   |
                     | destination=Goa   |
                     | flight=true       |
                     | hotel=true        |
                     +---------+---------+
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
       +-------------------+       +-------------------+
       |   Flight Node     |       |    Hotel Node     |
       +---------+---------+       +---------+---------+
                 |                           |
                 | HTTP                      | HTTP
                 v                           v
       +-------------------+       +-------------------+
       |   Flight Agent    |       |    Hotel Agent    |
       +---------+---------+       +---------+---------+
                 |                           |
                 | MCP                       | MCP
                 v                           v
       +-------------------+       +-------------------+
       | search_flights    |       | search_hotels     |
       +---------+---------+       +---------+---------+
                 |                           |
                 v                           v
          Flight Results              Hotel Results
                 |                           |
                 +-------------+-------------+
                               |
                               v
                      +----------------+
                      |   build_plan   |
                      +-------+--------+
                              |
                    +---------+---------+
                    |                   |
                    v                   v
              Cheapest Flight     Highest-rated
                                      Hotel
                    |                   |
                    +---------+---------+
                              |
                              v
                       Calculate Costs
                              |
                              v
                       +--------------+
                       |  TravelPlan  |
                       +------+-------+
                              |
                              v
                            USER
```

 ## Summary

 The **Travel Router Agent is the orchestrator** of the entire travel system.

 Its flow is:

```
User Request
     ↓
Travel Router
     ↓
Router LLM
     ↓
RouterDecision
     ↓
┌───────────────┬────────────────┐
│               │                │
↓               ↓                ↓
Flight Agent   Hotel Agent      ...
│               │
↓               ↓
MCP            MCP
│               │
↓               ↓
Flights        Hotels
│               │
└───────┬───────┘
        ↓
   Build Plan
        ↓
Select cheapest flight
        ↓
Select highest-rated hotel
        ↓
Calculate total cost
        ↓
TravelPlan
        ↓
Final JSON Response
```

 **In one sentence:**

 > The Travel Router Agent acts as the coordinator: it uses an LLM to understand the user's travel request, calls the required Flight and Hotel Agents over HTTP, receives their results, selects the cheapest flight and highest-rated hotel, calculates the estimated trip cost, builds a `TravelPlan`, and returns the complete travel itinerary.