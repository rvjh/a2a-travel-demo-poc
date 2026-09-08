## POC Implementation — Step-by-Step

 This POC was built incrementally, starting with the MCP tools, then adding individual agents, orchestration, and finally the travel gateway.

### 1\. Create the Project Structure

 First, create the basic project structure:

```
a2a-travel-demo-poc/
│
├── agents/
│   ├── flight_agent/
│   │   └── main.py
│   │
│   ├── hotel_agent/
│   │   └── main.py
│   │
│   └── router_agent/
│       └── main.py
│
├── common/
│   ├── config.py
│   ├── llm.py
│   └── models.py
│
├── gateway/
│   └── main.py
│
├── mcp_gateway/
│   └── main.py
│
├── tests/
│   ├── check_mcp_tools.py
│   ├── test_mcp.py
│   └── test_agent.py
│
├── run_all.py
└── README.md
```

---

### 2\. Configure the MCP Gateway

 **File:**

```
mcp_gateway/main.py
```

 The first actual component developed was the **MCP Gateway**.

 The MCP Gateway contains the travel tools and sample travel data.

 Tools exposed by the MCP Gateway:

```
search_flights
flight_price
search_hotels
hotel_price
```

 The MCP server uses Streamable HTTP:

```
http://127.0.0.1:9000/mcp
```

 The MCP Gateway is intentionally kept as a separate process.

---

### 3\. Configure Common Settings

 **File:**

```
common/config.py
```

 This file contains shared configuration such as the MCP Gateway URL and agent URLs.

 Example:

```
MCP Gateway
    ↓
http://127.0.0.1:9000/mcp
```

 Keeping these values in one place prevents URLs from being hard-coded throughout the application.

---

### 4\. Create Shared Data Models

 **File:**

```
common/models.py
```

 The common models define the data exchanged between the different components.

 Examples include:

```
AgentCard
AgentRequest
Flight
Hotel
FlightAgentResult
HotelAgentResult
TravelPlan
```

 This provides a consistent structure for communication between the agents and gateway.

---

### 5\. Configure the LLM

 **File:**

```
common/llm.py
```

 The LLM configuration was added so that individual agents can use the same LLM setup.

 The LLM is primarily used for:

- Understanding the available results.
- Selecting the best flight.
- Selecting the best hotel.
- Generating a concise recommendation.

 The agents are instructed to use only the data returned by the MCP tools.

---

### 6\. Build the Flight Agent

 **File:**

```
agents/flight_agent/main.py
```

 The Flight Agent was created after the MCP Gateway.

 Its responsibility is:

```
Flight request
     ↓
Flight Agent
     ↓
MCP Gateway
     ↓
search_flights
     ↓
Flight Agent
     ↓
LLM recommendation
```

 The Flight Agent exposes:

```
GET  /health
GET  /.well-known/agent-card.json
POST /
```

 The agent calls the MCP tool:

```
search_flights
```

 The MCP tool returns flight information such as:

```
Airline
Flight number
From city
Destination
Price
Currency
Duration
```

 The Flight Agent then uses the LLM to recommend the best available flight.

---

### 7\. Test the MCP Tools

 **File:**

```
tests/check_mcp_tools.py
```

 Before building the complete agent flow, the MCP tools were tested independently.

 Run:

```
python -m tests.check_mcp_tools
```

 Expected result:

```
Connected to MCP server.

Available MCP tools:
------------------------------------------------------------
search_flights
flight_price
search_hotels
hotel_price
------------------------------------------------------------
```

 This step verifies that the MCP Gateway is running correctly and that the expected tools are available.

---

### 8\. Build the Hotel Agent

 **File:**

```
agents/hotel_agent/main.py
```

 The Hotel Agent was then created.

 Its responsibility is:

```
Hotel request
     ↓
Hotel Agent
     ↓
MCP Gateway
     ↓
search_hotels
     ↓
Hotel Agent
     ↓
LLM recommendation
```

 The Hotel Agent calls:

```
search_hotels
```

 and receives hotel information such as:

```
Hotel name
Destination
Price per night
Currency
Rating
Number of nights
```

 The LLM then selects the recommended hotel.

---

### 9\. Test Individual Agents

 Once the Flight and Hotel Agents were working, each agent could be tested independently.

 For example:

```
Client
  ↓
Flight Agent :8001
  ↓
MCP Gateway :9000
```

 and:

```
Client
  ↓
Hotel Agent :8002
  ↓
MCP Gateway :9000
```

 This makes it easier to identify whether a problem is in the agent or the MCP layer.

---

### 10\. Build the Router Agent

 **File:**

```
agents/router_agent/main.py
```

 After the individual agents were working, the Router Agent was introduced.

 The Router Agent is responsible for orchestration.

 It uses **LangGraph** to coordinate the agents.

 The flow becomes:

```
User Request
     ↓
Router Agent
     │
     ├──────────────► Flight Agent
     │
     └──────────────► Hotel Agent
```

 For a request such as:

```
Plan a 3 day trip to Goa
```

 the Router Agent identifies that both flight and hotel information are required.

 It therefore calls:

```
Flight Agent
Hotel Agent
```

 The results are then combined into a single travel plan.

---

### 11\. Build the Travel Gateway

 **File:**

```
gateway/main.py
```

 The Travel Gateway was added as the main entry point for clients.

 The external request flow is:

```
Client
  ↓
Travel Gateway :8000
  ↓
Router Agent :8003
  ↓
Flight Agent :8001
  ↓
MCP Gateway :9000
```

 and:

```
Router Agent :8003
  ↓
Hotel Agent :8002
  ↓
MCP Gateway :9000
```

 The main endpoint is:

```
POST /plan
```

 The client does not need to directly communicate with the individual agents.

---

### 12\. Add End-to-End Testing

 **File:**

```
tests/test_agent.py
```

 The final test validates the complete system.

 Three scenarios were tested:

#### Scenario 1 — Complete Trip

```
Plan a 3 day trip to Goa
```

 Expected behavior:

```
Travel Gateway
      ↓
Router Agent
      ↓
 ┌────┴────┐
 ↓         ↓
Flight    Hotel
Agent     Agent
 ↓         ↓
MCP       MCP
 ↓         ↓
Flight    Hotel
results   results
 └────┬────┘
      ↓
Combined Travel Plan
```

#### Scenario 2 — Flight Only

```
Find a flight to Goa
```

 Expected behavior:

```
Travel Gateway
      ↓
Router Agent
      ↓
Flight Agent
      ↓
MCP Gateway
      ↓
Flight result
```

 The Hotel Agent should not be called.

#### Scenario 3 — Hotel Only

```
Find a hotel in Goa
```

 Expected behavior:

```
Travel Gateway
      ↓
Router Agent
      ↓
Hotel Agent
      ↓
MCP Gateway
      ↓
Hotel result
```

 The Flight Agent should not be called.

---

### 13\. Create `run_all.py`

 **File:**

```
run_all.py
```

 Once all components were working independently, `run_all.py` was added to simplify local development.

 The MCP Gateway is **not started by `run_all.py`** because it is already running separately on:

```
http://127.0.0.1:9000/mcp
```

 `run_all.py` starts:

```
Flight Agent     :8001
Hotel Agent      :8002
Router Agent     :8003
Travel Gateway   :8000
```

 Run:

```
python run_all.py
```

---

## Final Startup Sequence

 The final development workflow is:

### Terminal 1 — MCP Gateway

 Start the MCP Gateway:

```
python mcp_gateway\main.py
```

 Verify it:

```
python -m tests.check_mcp_tools
```

---

### Terminal 2 — All A2A Services

 Start:

```
python run_all.py
```

 This starts:

```
Flight Agent     → 8001
Hotel Agent      → 8002
Router Agent     → 8003
Travel Gateway   → 8000
```

---

### Terminal 3 — End-to-End Test

 Run:

```
python -m tests.test_agent
```

---

## Complete POC Flow

 The final architecture and implementation flow is:

```
                         USER / CLIENT
                              │
                              ▼
                   ┌────────────────────┐
                   │  Travel Gateway    │
                   │      :8000         │
                   │                    │
                   │    POST /plan      │
                   └─────────┬──────────┘
                             │
                             ▼
                   ┌────────────────────┐
                   │   Router Agent     │
                   │      :8003         │
                   │                    │
                   │     LangGraph      │
                   └──────┬───────┬─────┘
                          │       │
                ┌─────────┘       └─────────┐
                ▼                           ▼
       ┌────────────────┐          ┌────────────────┐
       │ Flight Agent   │          │  Hotel Agent   │
       │     :8001      │          │     :8002      │
       └───────┬────────┘          └───────┬────────┘
               │                           │
               └─────────────┬─────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    MCP Gateway      │
                  │       :9000         │
                  │                     │
                  │ search_flights      │
                  │ flight_price        │
                  │ search_hotels       │
                  │ hotel_price         │
                  └─────────────────────┘
```

## Development Order

 The POC was implemented in this order:

```
1.  Project structure
        ↓
2.  MCP Gateway
        ↓
3.  Common configuration
        ↓
4.  Common models
        ↓
5.  LLM configuration
        ↓
6.  MCP tool testing
        ↓
7.  Flight Agent
        ↓
8.  Hotel Agent
        ↓
9.  Individual agent testing
        ↓
10. Router Agent + LangGraph
        ↓
11. Travel Gateway
        ↓
12. End-to-end testing
        ↓
13. run_all.py
```

 This gives the POC a clear progression from **MCP tools → individual A2A agents → orchestration → API gateway → end-to-end travel planning**.
