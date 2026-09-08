# Testing Flow

 The testing script is used to verify the complete **Travel Agent → Flight Agent / Hotel Agent → MCP Tools → LLM** flow.

 The test script sends multiple travel scenarios to the Travel Agent and saves the response of each scenario as an HTML report.

---

 ## Overall Testing Flow

```
                    Test Script
                         |
                         | POST /plan
                         v
                 +----------------+
                 |  Travel Agent  |
                 +-------+--------+
                         |
             +-----------+-----------+
             |                       |
             v                       v
       Flight Agent            Hotel Agent
             |                       |
             v                       v
      search_flights          search_hotels
             |                       |
             v                       v
        MCP Gateway             MCP Gateway
             |                       |
             +-----------+-----------+
                         |
                         v
                  Agent Results
                         |
                         v
                  Travel Plan
                         |
                         v
                  Test Script
                    /       \
                   v         v
              Console      HTML Report
```

---

 # Test Server

 The testing script uses:

```
BASE_URL = "http://127.0.0.1:8000"
```

 This means the test script expects the main Travel Agent to be running on:

```
http://127.0.0.1:8000
```

 The test script sends requests to:

```
POST http://127.0.0.1:8000/plan
```

---

 # Test Scenarios

 The script defines three scenarios.

```
SCENARIOS = [
    ...
]
```

 These scenarios test different parts of the system.

---

 ## Scenario 1: Complete Trip Planning

 Request:

```
Plan a 3 day trip to Goa.
Find me a flight and hotel.
```

 Flow:

```
Test Script
     |
     | POST /plan
     v
Travel Agent
     |
     +-------------------+
     |                   |
     v                   v
Flight Agent         Hotel Agent
     |                   |
     v                   v
search_flights       search_hotels
     |                   |
     v                   v
Flight Result        Hotel Result
     |                   |
     +---------+---------+
               |
               v
          Travel Plan
               |
               v
          Test Script
```

 This is the most complete test because it verifies both:

 - Flight Agent
- Hotel Agent

 and their corresponding MCP tools.

 Expected tools:

```
search_flights
search_hotels
```

 Expected agents:

```
flight-agent
hotel-agent
```

---

 # Scenario 2: Flight Search

 Request:

```
Find me the best flight to Goa.
```

 Flow:

```
Test Script
     |
     | POST /plan
     v
Travel Agent
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
Flight Data
     |
     v
Flight Agent
     |
     v
LLM Recommendation
     |
     v
Travel Agent
     |
     v
Test Script
```

 This scenario primarily tests the **Flight Agent flow**.

 Expected tool:

```
search_flights
```

 Expected agent:

```
flight-agent
```

---

 # Scenario 3: Hotel Search

 Request:

```
Find me a good hotel in Goa
for a 3 day trip.
```

 Flow:

```
Test Script
     |
     | POST /plan
     v
Travel Agent
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
Hotel Data
     |
     v
Hotel Agent
     |
     v
LLM Recommendation
     |
     v
Travel Agent
     |
     v
Test Script
```

 This scenario primarily tests the **Hotel Agent flow**.

 Expected tool:

```
search_hotels
```

 Expected agent:

```
hotel-agent
```

---

 # How the Test Script Executes

 The entry point is:

```
if __name__ == "__main__":
    main()
```

 When the Python file is executed, `main()` is called.

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

 The script loops through all three scenarios.

```
main()
  |
  +--> Scenario 1
  |
  +--> Scenario 2
  |
  +--> Scenario 3
```

 Each scenario is executed **sequentially**.

---

 # `run_scenario()` Flow

 For every scenario, the script calls:

```
run_scenario(
    index,
    scenario,
)
```

 The first thing it does is print the scenario name.

 Example:

```
========================================
Scenario 1: Plan a 3 day trip to Goa
========================================
```

---

 # Step 1: Start Latency Timer

 The script records the start time:

```
started = time.perf_counter()
```

 This is used to calculate how long the request takes.

---

 # Step 2: Send Request to Travel Agent

 The main test request is:

```
response = requests.post(
    f"{BASE_URL}/plan",
    json={
        "message": scenario["message"]
    },
    timeout=120,
)
```

 For Scenario 1, this becomes:

```
POST http://127.0.0.1:8000/plan
```

 with:

```
{
  "message": "Plan a 3 day trip to Goa. Find me a flight and hotel."
}
```

 The flow is:

```
Test Script
     |
     | HTTP POST
     v
127.0.0.1:8000
     |
     v
/plan
     |
     v
Travel Agent
```

---

 # Step 3: Measure Latency

 After the Travel Agent responds:

```
latency_ms = int(
    (time.perf_counter() - started)
    * 1000
)
```

 The script calculates the total request duration.

 For example:

```
Latency: 2350 ms
```

 This measures the complete request time from the test script's perspective.

---

 # Step 4: Validate HTTP Response

 The script executes:

```
response.raise_for_status()
```

 If the server returns a successful HTTP status, execution continues.

 For example:

```
200 OK
```

 If the server returns an error such as:

```
400
500
```

 `raise_for_status()` raises an exception and the test stops unless additional error handling is added.

---

 # Step 5: Convert Response to JSON

 The response is converted into a Python dictionary:

```
payload = response.json()
```

 For example:

```
{
  "status": "completed",
  "travel_plan": {
    "destination": "goa",
    "flight": {},
    "hotel": {}
  },
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

 Now the test script can inspect the returned information.

---

 # Step 6: Print Status

 The script prints:

```
print(
    f"Status: "
    f"{payload.get('status', 'completed')}"
)
```

 Example:

```
Status: completed
```

 If `status` is missing, it uses:

```
completed
```

 as the default.

---

 # Step 7: Print Latency

 The script prints:

```
print(
    f"Latency: {latency_ms} ms"
)
```

 Example:

```
Latency: 2350 ms
```

 This helps measure the performance of the complete agent workflow.

---

 # Step 8: Print Travel Plan

 The script prints:

```
print("Agent says:")
```

 Then:

```
print(
    json.dumps(
        payload.get("travel_plan"),
        indent=2,
        ensure_ascii=False,
    )
)
```

 This displays the actual travel plan returned by the Travel Agent.

 Example:

```
Agent says:

{
  "destination": "goa",
  "flight": {
    "airline": "IndiGo",
    "price": 4500
  },
  "hotel": {
    "name": "Hotel A",
    "rating": 4.5,
    "price": 5000
  }
}
```

---

 # Step 9: Show Agents Called

 The script prints:

```
payload.get(
    "agents_called",
    [],
)
```

 Example:

```
Agents called: ['flight-agent', 'hotel-agent']
```

 For a flight-only scenario:

```
Agents called: ['flight-agent']
```

 For a hotel-only scenario:

```
Agents called: ['hotel-agent']
```

---

 # Step 10: Show Tools Called

 The script prints:

```
payload.get(
    "tools_called",
    [],
)
```

 For Scenario 1:

```
Tools called: ['search_flights', 'search_hotels']
```

 For Scenario 2:

```
Tools called: ['search_flights']
```

 For Scenario 3:

```
Tools called: ['search_hotels']
```

 This is useful because it allows you to verify whether the correct MCP tools were actually used.

---

 # Step 11: Generate HTML Report

 After the scenario completes:

```
report = save_report(
    scenario_number,
    payload,
)
```

 The complete response is passed to `save_report()`.

 The function creates the `reports` directory if it doesn't already exist:

```
os.makedirs(
    "reports",
    exist_ok=True,
)
```

 Then it creates a filename:

```
filename = (
    f"reports/scenario"
    f"{scenario_number}-0.html"
)
```

 The resulting files are:

```
reports/
├── scenario1-0.html
├── scenario2-0.html
└── scenario3-0.html
```

---

 # Report Generation Flow

 The response JSON is formatted:

```
pretty_json = json.dumps(
    payload,
    indent=2,
    ensure_ascii=False,
)
```

 Then it is inserted into an HTML page.

 The generated report contains:

```
Travel Agent Report
        |
        v
Complete JSON Response
```

 For example:

```
<h1>Travel Agent Report</h1>

<pre>
{
  "status": "completed",
  "travel_plan": {...},
  "agents_called": [...],
  "tools_called": [...]
}
</pre>
```

 Finally, the file is written:

```
with open(
    filename,
    "w",
    encoding="utf-8",
) as file:

    file.write(html)
```

---

 # Complete Testing Flow

 The complete testing architecture is:

```
                         TEST SCRIPT
                              |
                              |
                       SCENARIOS[]
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
          Scenario 1      Scenario 2      Scenario 3
          Trip Planning   Flight Search   Hotel Search
              |               |               |
              +---------------+---------------+
                              |
                              v
                    POST /plan
                              |
                              v
                    +----------------+
                    |  Travel Agent  |
                    +-------+--------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
        Flight Agent                Hotel Agent
              |                           |
              v                           v
      search_flights               search_hotels
              |                           |
              v                           v
        MCP Gateway                 MCP Gateway
              |                           |
              v                           v
        Flight Data                  Hotel Data
              |                           |
              v                           v
       Flight Agent                 Hotel Agent
              |                           |
              v                           v
            LLM                         LLM
              |                           |
              +-------------+-------------+
                            |
                            v
                      Travel Plan
                            |
                            v
                      HTTP Response
                            |
                            v
                       Test Script
                       /    |    \
                      /     |     \
                     v      v      v
                  Status Latency  Plan
                            |
                            v
                     Agents Called
                            |
                            v
                     Tools Called
                            |
                            v
                      HTML Report
```

---

 # Scenario Execution Order

 The test does **not** run all scenarios simultaneously.

 It runs them one by one:

```
main()
  |
  v
Scenario 1
  |
  | complete
  v
Scenario 2
  |
  | complete
  v
Scenario 3
  |
  | complete
  v
Program finished
```

 So the final `reports/` directory contains one report for each scenario:

```
reports/
├── scenario1-0.html
├── scenario2-0.html
└── scenario3-0.html
```

---

 # Final Testing Flow Summary

```
Test Script starts
       ↓
Load 3 scenarios
       ↓
Run Scenario 1
       ↓
POST /plan
       ↓
Travel Agent
       ↓
Flight Agent + Hotel Agent
       ↓
MCP Tools
       ↓
LLM Recommendations
       ↓
Travel Plan
       ↓
Response received
       ↓
Measure latency
       ↓
Print result
       ↓
Save scenario1-0.html
       ↓
Run Scenario 2
       ↓
POST /plan
       ↓
Flight Agent
       ↓
search_flights
       ↓
LLM
       ↓
Response
       ↓
Save scenario2-0.html
       ↓
Run Scenario 3
       ↓
POST /plan
       ↓
Hotel Agent
       ↓
search_hotels
       ↓
LLM
       ↓
Response
       ↓
Save scenario3-0.html
       ↓
Testing complete
```

 **In short:**

 > The test script acts as the client. It sends three predefined travel requests to the Travel Agent's `/plan` endpoint, measures the response time, displays the returned travel plan and records which agents and MCP tools were used. After each test, it saves the complete response as an HTML report for later inspection.