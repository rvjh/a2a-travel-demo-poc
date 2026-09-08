# Running the A2A Travel Demo

 This project contains an MCP Gateway, multiple A2A agents, a Router Agent, and a Travel Gateway.

 You can run the system in two ways:

 1. **Manual mode** — start each service one by one.
2. **Automatic mode** — start all services using `run_all.py`.

---

 # Architecture

 The complete system looks like this:

```
                         Client / Test
                              |
                              v
                    +-------------------+
                    |  Travel Gateway   |
                    |   Port: 8000      |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |   Router Agent    |
                    |   Port: 8003      |
                    +---------+---------+
                              |
                    +---------+---------+
                    |                   |
                    v                   v
             +-------------+     +-------------+
             | Flight Agent|     | Hotel Agent |
             | Port: 8001  |     | Port: 8002  |
             +------+------+     +------+------+
                    |                   |
                    +---------+---------+
                              |
                              v
                    +-------------------+
                    |    MCP Gateway    |
                    |   Port: 9000      |
                    +---------+---------+
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          Flight MCP Tools          Hotel MCP Tools
          search_flights            search_hotels
          flight_price              hotel_price
```

---

 # Service Ports

 | Service | Port | Purpose |
| --- | --- | --- |
| MCP Gateway | `9000` | Provides MCP tools |
| Flight Agent | `8001` | Flight search and recommendation |
| Hotel Agent | `8002` | Hotel search and recommendation |
| Router Agent | `8003` | Routes requests to agents |
| Travel Gateway | `8000` | Main entry point |

---

 # Option 1 — Run Manually

 In manual mode, each service is started separately.

 You will need multiple terminals.

---

 ## Terminal 1 — Start MCP Gateway

 Start the MCP Gateway first:

```
python mcp_gateway\main.py
```

 The MCP Gateway should start on:

```
http://127.0.0.1:9000/mcp
```

 The MCP Gateway provides these tools:

```
search_flights
flight_price
search_hotels
hotel_price
```

 ### MCP Architecture

```
MCP Gateway
    |
    +-- search_flights
    |
    +-- flight_price
    |
    +-- search_hotels
    |
    +-- hotel_price
```

---

 # Test MCP Gateway

 After starting the MCP Gateway, open another terminal and verify that the MCP server is responding.

 ## Test 1 — Direct MCP Test

 Run:

```
python tests/test_mcp.py
```

 This test connects directly to:

```
http://127.0.0.1:9000/mcp
```

 and verifies:

```
Connection
    ↓
Tool Discovery
    ↓
search_flights
    ↓
flight_price
    ↓
search_hotels
    ↓
hotel_price
```

---

 ## Test 2 — Check MCP Tools

 You can also run:

```
python -m tests.check_mcp_tools
```

 This verifies that the expected MCP tools are available.

 Expected tools:

```
search_flights
flight_price
search_hotels
hotel_price
```

 ### Recommended order

 After starting the MCP Gateway:

```
python tests/test_mcp.py
```

 or:

```
python -m tests.check_mcp_tools
```

 Make sure the MCP tests pass before moving to the agents.

---

 # Terminal 2 — Start Flight Agent

 Start the Flight Agent:

```
uvicorn agents.flight_agent.main:app --host 127.0.0.1 --port 8001
```

 The Flight Agent runs on:

```
http://127.0.0.1:8001
```

 Its responsibility is:

```
Flight Request
      ↓
Flight Agent
      ↓
MCP Gateway
      ↓
search_flights
      ↓
Flight Data
      ↓
LLM Recommendation
      ↓
Flight Agent Result
```

---

 # Test Flight Agent

 Open another terminal and run:

```
curl -X POST http://127.0.0.1:8001/ ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Find me a flight to Goa\"}"
```

 The request goes directly to the Flight Agent.

```
curl
  |
  | POST /
  v
Flight Agent :8001
  |
  v
search_flights
  |
  v
MCP Gateway :9000
  |
  v
Flight Results
  |
  v
LLM
  |
  v
FlightAgentResult
```

 If the response is successful, the Flight Agent is working correctly.

---

 # Terminal 3 — Start Router Agent

 Start the Router Agent:

```
uvicorn agents.router_agent.main:app --host 127.0.0.1 --port 8003
```

 The Router Agent runs on:

```
http://127.0.0.1:8003
```

 Its responsibility is to determine which agent should handle a request.

 Conceptually:

```
User Request
      |
      v
Router Agent
      |
      +---- Flight request ---> Flight Agent
      |
      +---- Hotel request ----> Hotel Agent
      |
      +---- Travel request ---> Appropriate Agent(s)
```

---

 # Router Agent API Documentation

 FastAPI automatically provides Swagger/OpenAPI documentation.

 Open the following URL in your browser:

```
http://127.0.0.1:8003/docs
```

 This allows you to inspect and test the Router Agent APIs interactively.

---

 # Terminal 4 — Start Travel Gateway

 Start the main Travel Gateway:

```
uvicorn gateway.main:app --host 127.0.0.1 --port 8000
```

 The Travel Gateway runs on:

```
http://127.0.0.1:8000
```

 This is the main entry point for the complete travel planning flow.

 The architecture becomes:

```
Client
  |
  v
Travel Gateway :8000
  |
  v
Router Agent :8003
  |
  +------------+------------+
  |                         |
  v                         v
Flight Agent :8001     Hotel Agent :8002
  |                         |
  +------------+------------+
               |
               v
        MCP Gateway :9000
```

---

 # Health Check

 You can check whether the Flight Agent is running with:

```
curl http://127.0.0.1:8001/health
```

 If a health endpoint is implemented, you should receive a successful response.

 You can similarly expose health endpoints for the other services if required.

---

 # Terminal 5 — Run Complete Agent Test

 Once all required services are running, open another terminal and run:

```
python tests\test_agent.py
```

 This test sends travel requests through the main Travel Gateway.

 The test flow is:

```
test_agent.py
      |
      | POST /plan
      v
Travel Gateway :8000
      |
      v
Router Agent :8003
      |
      +--------------------+
      |                    |
      v                    v
Flight Agent          Hotel Agent
   :8001                 :8002
      |                    |
      +---------+----------+
                |
                v
        MCP Gateway :9000
                |
        +-------+-------+
        |               |
        v               v
 Flight Tools       Hotel Tools
        |               |
        +-------+-------+
                |
                v
          Agent Results
                |
                v
          Travel Plan
                |
                v
          test_agent.py
```

---

 # Manual Startup Order

 The recommended startup order is:

```
1. MCP Gateway
       ↓
2. Test MCP
       ↓
3. Flight Agent
       ↓
4. Test Flight Agent
       ↓
5. Hotel Agent
       ↓
6. Router Agent
       ↓
7. Travel Gateway
       ↓
8. Test Complete Agent Flow
```

 For the services specifically:

```
# Terminal 1
python mcp_gateway\main.py
```

 Then test:

```
python tests/test_mcp.py
```

 Then start:

```
# Terminal 2
uvicorn agents.flight_agent.main:app --host 127.0.0.1 --port 8001
```

 Then test:

```
curl -X POST http://127.0.0.1:8001/ ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Find me a flight to Goa\"}"
```

 Then:

```
# Terminal 3
uvicorn agents.router_agent.main:app --host 127.0.0.1 --port 8003
```

 Then:

```
# Terminal 4
uvicorn gateway.main:app --host 127.0.0.1 --port 8000
```

 Finally:

```
# Terminal 5
python tests\test_agent.py
```

---

 # Option 2 — Run Everything Automatically

 If you don't want to start every service manually, the project provides:

```
run_all.py
```

 After everything has been installed and configured, simply run:

```
python run_all.py
```

 The `run_all.py` script starts the required services for you.

 The expected architecture is:

```
                    run_all.py
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
 MCP Gateway       Flight Agent     Hotel Agent
   :9000              :8001            :8002
        |               |               |
        +---------------+---------------+
                        |
                        v
                  Router Agent
                     :8003
                        |
                        v
                 Travel Gateway
                     :8000
```

---

 # After `run_all.py`

 Once all services have started, open another terminal.

 Run:

```
python tests/test_agent.py
```

 This performs the end-to-end test.

```
test_agent.py
      |
      v
Travel Gateway
      |
      v
Router Agent
      |
      +---------> Flight Agent
      |               |
      |               v
      |          MCP Gateway
      |
      +---------> Hotel Agent
                      |
                      v
                 MCP Gateway
                      |
                      v
                 Final Plan
```

---

 # Recommended Testing Strategy

 For debugging, it is better to test from the bottom layer upward.

 ## Level 1 — MCP

 First verify:

```
python tests/test_mcp.py
```

 This confirms:

```
MCP connection ✓
Tool discovery ✓
Flight tools ✓
Hotel tools ✓
```

---

 ## Level 2 — Individual Agents

 Test the Flight Agent:

```
curl -X POST http://127.0.0.1:8001/ ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Find me a flight to Goa\"}"
```

 Then test the Hotel Agent similarly if an endpoint is available.

---

 ## Level 3 — Router

 Open:

```
http://127.0.0.1:8003/docs
```

 Use Swagger to verify the Router Agent.

---

 ## Level 4 — Complete Travel Flow

 Finally run:

```
python tests\test_agent.py
```

 This verifies the complete system.

---

 # Quick Start

 If everything is already installed, the easiest approach is:

 ### Terminal 1

```
python run_all.py
```

 ### Terminal 2

```
python tests/test_agent.py
```

 That's it.

---

 # Quick Reference

 | Action | Command |
| --- | --- |
| Start MCP Gateway | `python mcp_gateway\main.py` |
| Test MCP | `python tests/test_mcp.py` |
| Check MCP tools | `python -m tests.check_mcp_tools` |
| Start Flight Agent | `uvicorn agents.flight_agent.main:app --host 127.0.0.1 --port 8001` |
| Start Router Agent | `uvicorn agents.router_agent.main:app --host 127.0.0.1 --port 8003` |
| Start Travel Gateway | `uvicorn gateway.main:app --host 127.0.0.1 --port 8000` |
| Test complete system | `python tests\test_agent.py` |
| Start everything | `python run_all.py` |
| Router Swagger | `http://127.0.0.1:8003/docs` |

---

 # Final Flow

 The complete application flow is:

```
                         USER
                           |
                           v
                    test_agent.py
                           |
                           v
                  Travel Gateway :8000
                           |
                           v
                    Router Agent :8003
                           |
             +-------------+-------------+
             |                           |
             v                           v
      Flight Agent :8001          Hotel Agent :8002
             |                           |
             |                           |
             +-------------+-------------+
                           |
                           v
                   MCP Gateway :9000
                           |
             +-------------+-------------+
             |                           |
             v                           v
      Flight MCP Tools             Hotel MCP Tools
             |                           |
             +-------------+-------------+
                           |
                           v
                    Tool Results
                           |
                           v
                   Agent Reasoning
                           |
                           v
                    Travel Plan
                           |
                           v
                         USER
```

 The recommended approach is **MCP → individual agents → Router → Travel Gateway → end-to-end test**. This makes it much easier to identify which layer has a problem if a test fails.