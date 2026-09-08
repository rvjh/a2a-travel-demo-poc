# Testing

The testing setup verifies the Travel Agent system from the bottom layer upward.

The recommended testing order is:

1. Test the MCP Gateway
2. Check available MCP tools
3. Test the complete Agent flow

The overall architecture is:

```text
                        Testing
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
        MCP Test      Check MCP Tools   Agent Tests
            |              |              |
            v              v              v
       MCP Gateway     MCP Gateway    Travel Gateway
                                         |
                              +----------+----------+
                              |                     |
                              v                     v
                        Flight Agent           Hotel Agent
                              |                     |
                              v                     v
                        MCP Gateway            MCP Gateway
```

---

# 1\. Test the MCP Gateway

 The first test should always verify that the MCP Gateway is working correctly.

 Run:

```
python tests/test_mcp.py
```

 This test connects directly to:

```
http://127.0.0.1:9000/mcp
```

 using the FastMCP client.

 The test verifies:

- MCP server connection
- Available MCP tools
- Flight search
- Cheapest flight price
- Hotel search
- Cheapest hotel price

---

## MCP Test Flow

```
test_mcp.py
     |
     | Connect
     v
MCP Gateway
     |
     +------------------+
     |                  |
     v                  v
Flight Tools        Hotel Tools
     |                  |
     v                  v
search_flights      search_hotels
flight_price        hotel_price
```

---

## MCP Connection

 The test creates a FastMCP client:

```
async with Client(MCP_URL) as client:
```

 where:

```
MCP_URL =
http://127.0.0.1:9000/mcp
```

 If the connection succeeds, the test prints:

```
Connected successfully!
```

---

# 2\. Check Available MCP Tools

 The project also contains:

```
tests/check_mcp_tools.py
```

 Run:

```
python tests/check_mcp_tools.py
```

 This is a lightweight MCP discovery test.

 It connects to the MCP Gateway and calls:

```
tools = await client.list_tools()
```

 It then prints all available MCP tools.

 Expected tools are:

```
search_flights
flight_price
search_hotels
hotel_price
```

 The flow is:

```
check_mcp_tools.py
        |
        v
MCP Gateway
        |
        | list_tools()
        v
Available Tools
        |
        +--> search_flights
        +--> flight_price
        +--> search_hotels
        +--> hotel_price
```

 This test answers:

> "Is the MCP Gateway exposing the tools that the agents expect?"

---

# 3\. MCP Tool Testing

 The main MCP test also executes each tool.

## Flight Search

```
await client.call_tool(
    "search_flights",
    {
        "destination": "Goa",
    },
)
```

 This verifies:

```
search_flights
      |
      v
Goa flight data
```

---

## Flight Price

```
await client.call_tool(
    "flight_price",
    {
        "destination": "Goa",
    },
)
```

 This verifies that the MCP Gateway can calculate the cheapest flight price.

---

## Hotel Search

```
await client.call_tool(
    "search_hotels",
    {
        "destination": "Goa",
        "nights": 3,
    },
)
```

 This verifies:

```
search_hotels
      |
      v
Goa hotel data
      |
      v
3-night hotel prices
```

---

## Hotel Price

```
await client.call_tool(
    "hotel_price",
    {
        "destination": "Goa",
        "nights": 3,
    },
)
```

 This verifies the cheapest total hotel price for the requested number of nights.

---

# 4\. Complete Agent Testing

 After confirming that MCP works, test the complete agent system.

 Run:

```
python tests/test_agents.py
```

 The test script sends requests to the Travel Gateway:

```
http://127.0.0.1:8000/plan
```

 The complete flow is:

```
test_agents.py
      |
      | POST /plan
      v
Travel Gateway
      |
      v
Travel Router Agent
      |
      +------------------+
      |                  |
      v                  v
Flight Agent        Hotel Agent
      |                  |
      v                  v
MCP Tools            MCP Tools
      |                  |
      +--------+---------+
               |
               v
          Travel Plan
               |
               v
         Travel Gateway
               |
               v
          Test Script
```

---

# Test Scenarios

 The test script contains three scenarios.

```
SCENARIOS = [
    ...
]
```

 They are executed sequentially.

---

## Scenario 1: Complete Trip Planning

 Request:

```
Plan a 3 day trip to Goa.
Find me a flight and hotel.
```

 Expected flow:

```
Test Script
     |
     v
Travel Gateway
     |
     v
Router Agent
     |
     +------------+------------+
     |                         |
     v                         v
Flight Agent              Hotel Agent
     |                         |
     v                         v
search_flights            search_hotels
     |                         |
     +------------+------------+
                  |
                  v
             Travel Plan
```

 Expected agents:

```
flight-agent
hotel-agent
```

 Expected tools:

```
search_flights
search_hotels
```

 This is the most complete end-to-end test.

---

# Scenario 2: Flight Search

 Request:

```
Find me the best flight to Goa.
```

 Expected flow:

```
Test Script
     |
     v
Travel Gateway
     |
     v
Router Agent
     |
     v
Flight Agent
     |
     v
search_flights
     |
     v
MCP Gateway
     |
     v
Flight Result
```

 Expected agent:

```
flight-agent
```

 Expected tool:

```
search_flights
```

---

# Scenario 3: Hotel Search

 Request:

```
Find me a good hotel in Goa
for a 3 day trip.
```

 Expected flow:

```
Test Script
     |
     v
Travel Gateway
     |
     v
Router Agent
     |
     v
Hotel Agent
     |
     v
search_hotels
     |
     v
MCP Gateway
     |
     v
Hotel Result
```

 Expected agent:

```
hotel-agent
```

 Expected tool:

```
search_hotels
```

---

# Test Execution

 The `main()` function runs all scenarios:

```
def main():

    for index, scenario in enumerate(
        SCENARIOS,
        start=1,
    ):

        run_scenario(
            index,
            scenario,
        )
```

 Therefore, execution is sequential:

```
main()
  |
  v
Scenario 1
  |
  v
Scenario 2
  |
  v
Scenario 3
  |
  v
Testing Complete
```

---

# Latency Measurement

 Each agent request measures its total response time.

 The test starts a timer:

```
started = time.perf_counter()
```

 After the response:

```
latency_ms = int(
    (time.perf_counter() - started) * 1000
)
```

 The result is displayed as:

```
Latency: 2350 ms
```

 This measures the complete request from the test client to the Travel Gateway and back.

---

# Response Validation

 The test checks the HTTP response:

```
response.raise_for_status()
```

 A successful request should return:

```
200 OK
```

 The response is then converted to JSON:

```
payload = response.json()
```

---

# What the Test Displays

 For every scenario, the test prints:

```
Status
Latency
Travel Plan
Agents Called
Tools Called
```

 Example:

```
Status: completed
Latency: 2350 ms

Agents called:
['flight-agent', 'hotel-agent']

Tools called:
['search_flights', 'search_hotels']
```

 This makes it easy to verify that the correct agents and MCP tools were used.

---

# HTML Reports

 After each scenario, the response is saved as an HTML report.

 Reports are stored in:

```
reports/
```

 The files are:

```
reports/
├── scenario1-0.html
├── scenario2-0.html
└── scenario3-0.html
```

 Each report contains the complete JSON response from the Travel Gateway.

 The report includes:

```
Travel Agent Report
        |
        v
Complete JSON Response
        |
        +--> Travel Plan
        +--> Agents Called
        +--> Tools Called
        +--> Latency
```

---

# Recommended Testing Order

 The recommended order is:

```
1. Start MCP Gateway
        |
        v
2. python tests/test_mcp.py
        |
        v
3. python tests/check_mcp_tools.py
        |
        v
4. Start Flight / Hotel / Router / Travel Gateway
        |
        v
5. python tests/test_agents.py
```

 This approach makes debugging easier because the MCP layer is verified before testing the agents.

---

# Complete Testing Architecture

```
                         TESTING
                            |
                            v
                     +-------------+
                     | MCP Testing |
                     +------+------+
                            |
                +-----------+-----------+
                |                       |
                v                       v
          test_mcp.py         check_mcp_tools.py
                |                       |
                +-----------+-----------+
                            |
                            v
                     MCP Gateway
                      :9000/mcp
                            |
                +-----------+-----------+
                |                       |
                v                       v
          Flight Tools             Hotel Tools
                |                       |
                v                       v
       search_flights             search_hotels
       flight_price               hotel_price

                            |
                            v
                    Agent Testing
                            |
                            v
                    test_agents.py
                            |
                            v
                   Travel Gateway
                       :8000
                            |
                            v
                     POST /plan
                            |
                            v
                  Travel Router Agent
                       /       \
                      /         \
                     v           v
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
                    Test Response
                          |
                +---------+---------+
                |         |         |
                v         v         v
             Status    Latency    Reports
```

---

# Final Testing Flow

```
MCP Gateway
     |
     v
Test MCP Connection
     |
     v
List MCP Tools
     |
     v
Execute MCP Tools
     |
     v
MCP Testing Passed
     |
     v
Start Agent System
     |
     v
Run test_agents.py
     |
     v
POST /plan
     |
     v
Travel Router
     |
     +------------------+
     |                  |
     v                  v
Flight Agent        Hotel Agent
     |                  |
     v                  v
MCP Tools            MCP Tools
     |                  |
     +--------+---------+
              |
              v
         Travel Plan
              |
              v
        Test Response
              |
              v
         HTML Reports
```

## Summary

 The testing system validates the application in two stages:

1. **MCP testing** verifies the MCP Gateway, tool discovery, and individual tool execution.
2. **Agent testing** verifies the complete Travel Gateway → Router Agent → Flight/Hotel Agent → MCP → Travel Plan flow.
