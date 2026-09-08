# Travel Gateway

 ## Overview

 The **Travel Gateway** is the entry point for clients in the travel planning system.

 It exposes a simple API for creating travel plans and forwards the request to the **Travel Router Agent**.

 The Gateway does not perform flight or hotel searches itself.

```
Client
   |
   | POST /plan
   v
Travel Gateway
   |
   | HTTP
   v
Travel Router Agent
   |
   +--> Flight Agent
   |
   +--> Hotel Agent
   |
   v
Travel Plan
   |
   v
Gateway Response
```

---

 ## Main Responsibilities

 The Travel Gateway:

 - Accepts travel planning requests.
- Sends requests to the Router Agent.
- Handles Router Agent connection/errors.
- Measures request latency.
- Extracts agent and tool information.
- Returns a simplified travel plan response.

---

 ## API Endpoints

 ### Health Check

```
GET /
```

 Returns basic gateway information:

```
{
  "status": "ok",
  "service": "travel-gateway",
  "router_agent": "http://127.0.0.1:8000"
}
```

---

 ### Plan Trip

```
POST /plan
```

 Example request:

```
{
  "message": "Plan a 3 day trip to Goa with a flight and hotel."
}
```

 The Gateway forwards the request to:

```
ROUTER_AGENT_URL/
```

 using the shared `AgentRequest` model.

---

 ## Router Communication

 The Gateway uses `httpx.AsyncClient` to communicate with the Router Agent:

```
Travel Gateway
      |
      | HTTP POST
      v
Router Agent
      |
      v
Travel Plan
```

 The Router Agent is configured through:

```
common/config.py
```

 using:

```
ROUTER_AGENT_URL
```

---

 ## Error Handling

 If the Router Agent is unavailable or returns an HTTP error, the Gateway returns:

```
502 Bad Gateway
```

 with a message such as:

```
Router Agent unavailable
```

 This prevents internal Router errors from being exposed as successful responses.

---

 ## Latency Tracking

 The Gateway measures how long the Router request takes:

```
started = time.perf_counter()
```

 and returns:

```
{
  "latency_ms": 1250
}
```

 This is useful for monitoring system performance.

---

 ## Final Response

 The Gateway extracts information from the Router response and returns:

```
{
  "status": "completed",
  "latency_ms": 1250,
  "destination": "Goa",
  "duration_days": 3,
  "travel_plan": {},
  "agents_called": [
    "flight-agent",
    "hotel-agent"
  ],
  "tools_called": [
    "search_flights",
    "search_hotels"
  ]
}
```

---

 ## Agents and Tools Tracking

 The Gateway identifies which agents were used:

```
agents_called
    |
    +--> flight-agent
    +--> hotel-agent
```

 It also collects the tools used by those agents:

```
tools_called
    |
    +--> search_flights
    +--> search_hotels
```

 This provides visibility into the complete request flow.

---

 ## Overall Architecture

```
                  Client
                    |
                    | POST /plan
                    v
            +----------------+
            | Travel Gateway |
            +-------+--------+
                    |
                    | HTTP
                    v
            +----------------+
            | Router Agent   |
            +-------+--------+
                    |
             +------+------+
             |             |
             v             v
       Flight Agent   Hotel Agent
             |             |
             v             v
            MCP           MCP
             |             |
             +------+------+
                    |
                    v
              Travel Plan
                    |
                    v
             Travel Gateway
                    |
                    v
                  Client
```

 ## Key Point

 > **The Travel Gateway is the API entry point and coordinator-facing boundary. It receives client requests, forwards them to the Router Agent, handles errors and latency tracking, and returns a clean final travel-plan response.**