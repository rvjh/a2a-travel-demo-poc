# A2A Travel Agent POC

 A small **Travel Agent Proof of Concept (POC)** demonstrating how **A2A, MCP, LangGraph, Groq, Pydantic, and FastAPI** can work together in a multi-agent system.

 The project is intentionally small so that each architectural concept can be understood independently and then seen working together as one complete travel-planning workflow.

---

## What This POC Demonstrates

 This project combines the following concepts:

- **A2A (Agent-to-Agent)** — Router Agent communicates with Flight Agent and Hotel Agent.
- **MCP (Model Context Protocol)** — Agents consume travel tools from a centralized MCP Gateway.
- **LangGraph** — Router Agent orchestrates the multi-agent workflow.
- **Groq** — Provides LLM reasoning and structured output.
- **Pydantic** — Provides shared request and response contracts under `common/`.
- **FastAPI** — Provides the HTTP service boundary for each agent.
- **Testing** — Includes MCP tests and an end-to-end travel-agent test.
- **`run_all.py`** — Starts the A2A services automatically.
- **Agent Cards** — Flight, Hotel, and Router agents can expose their capabilities through `/.well-known/agent-card.json`.
- **Structured Responses** — Agent results are returned using Pydantic models.

---

# Architecture

```
                         A2A TRAVEL SYSTEM
                         =================

                    ┌─────────────────────────┐
                    │      MCP Gateway        │
                    │                         │
                    │    Streamable HTTP      │
                    │  127.0.0.1:9000/mcp    │
                    │                         │
                    │  MCP Tools:             │
                    │  • search_flights       │
                    │  • flight_price         │
                    │  • search_hotels        │
                    │  • hotel_price          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
          ┌──────────────────┐      ┌──────────────────┐
          │   Flight Agent   │      │    Hotel Agent   │
          │                  │      │                  │
          │   Port: 8001     │      │   Port: 8002     │
          │                  │      │                  │
          │ Uses MCP:        │      │ Uses MCP:        │
          │ search_flights   │      │ search_hotels    │
          │ flight_price     │      │ hotel_price      │
          └────────┬─────────┘      └────────┬─────────┘
                   │                         │
                   │        A2A HTTP         │
                   └────────────┬────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      Router Agent       │
                    │                         │
                    │      Port: 8003         │
                    │                         │
                    │  LangGraph orchestration│
                    │                         │
                    │  Routes to:             │
                    │  • Flight Agent         │
                    │  • Hotel Agent          │
                    └────────────┬────────────┘
                                 │
                                 │ HTTP
                                 ▼
                    ┌─────────────────────────┐
                    │     Travel Gateway      │
                    │                         │
                    │      Port: 8000         │
                    │                         │
                    │      POST /plan         │
                    │                         │
                    │  Main external API      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │     Client    │
                         │ / Test Agent  │
                         └───────────────┘
```

---

# Service Flow

 A user request enters through the Travel Gateway.

```
User / Client
      │
      ▼
Travel Gateway :8000
      │
      │ HTTP
      ▼
Router Agent :8003
      │
      ├──────────────► Flight Agent :8001
      │                       │
      │                       │ MCP
      │                       ▼
      │                MCP Gateway :9000
      │                       │
      │                       ▼
      │                search_flights
      │
      │
      └──────────────► Hotel Agent :8002
                              │
                              │ MCP
                              ▼
                       MCP Gateway :9000
                              │
                              ▼
                       search_hotels
```

 The Router Agent can call one or both specialist agents depending on the user's request.

 For example:

```
"Find me a flight to Goa"
        │
        ▼
Router Agent
        │
        ▼
Flight Agent
        │
        ▼
MCP Gateway
        │
        ▼
search_flights
```

 For:

```
"Plan a 3 day trip to Goa. Find me a flight and hotel."
```

 the flow becomes:

```
                    User Request
                         │
                         ▼
                 Travel Gateway
                         │
                         ▼
                  Router Agent
                    /        \
                   /          \
                  ▼            ▼
          Flight Agent     Hotel Agent
               │                │
               ▼                ▼
          MCP Gateway      MCP Gateway
               │                │
               ▼                ▼
        search_flights     search_hotels
               │                │
               └───────┬────────┘
                       │
                       ▼
                Combined Results
                       │
                       ▼
                  Travel Plan
```

---

# Communication Patterns

 This project demonstrates two different communication layers.

## A2A — Agent-to-Agent Communication

 A2A is used when one agent needs to communicate with another agent.

```
Router Agent
     |
     | HTTP POST
     v
Flight Agent
```

 and:

```
Router Agent
     |
     | HTTP POST
     v
Hotel Agent
```

 The Router Agent does not directly execute flight or hotel business logic.

 Instead, it delegates the task to the appropriate specialist agent.

---

## MCP — Tool Communication

 MCP is used when an agent needs to use a tool.

 For flights:

```
Flight Agent
     |
     | MCP / Streamable HTTP
     v
MCP Gateway
     |
     v
search_flights()
```

 For hotels:

```
Hotel Agent
     |
     | MCP / Streamable HTTP
     v
MCP Gateway
     |
     v
search_hotels()
```

 The MCP Gateway exposes the tools centrally.

---

# A2A vs MCP

 The architectural distinction is:

```
A2A
 |
 +--> Agent-to-Agent communication
 |
 +--> Agent discovery
 |
 +--> Agent capabilities
 |
 +--> Agent requests/responses
```

 Whereas:

```
MCP
 |
 +--> Tools
 |
 +--> Tool schemas
 |
 +--> Tool execution
 |
 +--> Tool results
```

 In simple terms:

> **A2A answers: "Which agent should I communicate with?"**

> **MCP answers: "Which tools can this agent use?"**

---

# Components

## MCP Gateway — Port 9000

 The MCP Gateway provides the travel-related MCP tools.

 Endpoint:

```
http://127.0.0.1:9000/mcp
```

 Available tools:

```
search_flights
flight_price
search_hotels
hotel_price
```

 The MCP Gateway runs separately from `run_all.py`.

 Start it with:

```
python mcp_gateway\main.py
```

---

## Flight Agent — Port 8001

 The Flight Agent handles flight-related requests.

 It:

1. Receives a request.
2. Determines the destination.
3. Calls the MCP Gateway.
4. Executes `search_flights`.
5. Converts the returned data into Pydantic models.
6. Uses the Groq LLM to recommend a flight.
7. Returns a structured `FlightAgentResult`.

 Endpoint:

```
http://127.0.0.1:8001
```

 Agent Card:

```
http://127.0.0.1:8001/.well-known/agent-card.json
```

 Skills:

```
flight_search
flight_price
```

---

## Hotel Agent — Port 8002

 The Hotel Agent handles hotel-related requests.

 It:

1. Receives a request.
2. Determines the destination and number of nights.
3. Calls the MCP Gateway.
4. Executes `search_hotels`.
5. Converts the returned data into Pydantic models.
6. Uses the Groq LLM to recommend a hotel.
7. Returns a structured `HotelAgentResult`.

 Endpoint:

```
http://127.0.0.1:8002
```

 Agent Card:

```
http://127.0.0.1:8002/.well-known/agent-card.json
```

 Skills:

```
hotel_search
hotel_price
```

---

## Router Agent — Port 8003

 The Router Agent is responsible for orchestration.

 It uses **LangGraph** to determine which specialist agents should be called.

 Conceptually:

```
User Request
      │
      ▼
Router Agent
      │
      ├── Flight required ──► Flight Agent
      │
      └── Hotel required ───► Hotel Agent
```

 The Router Agent then combines the specialist results into a travel plan.

 Endpoint:

```
http://127.0.0.1:8003
```

 Agent Card:

```
http://127.0.0.1:8003/.well-known/agent-card.json
```

 Swagger documentation:

```
http://127.0.0.1:8003/docs
```

---

## Travel Gateway — Port 8000

 The Travel Gateway is the main external HTTP entry point.

 It exposes:

```
POST /plan
```

 Example request:

```
{
  "message": "Plan a 3 day trip to Goa. Find me a flight and hotel."
}
```

 The Travel Gateway sends the request to the Router Agent.

```
Client
  │
  │ POST /plan
  ▼
Travel Gateway :8000
  │
  ▼
Router Agent :8003
```

---

# Ports

| Service        | Port     | Purpose             |
| -------------- | -------- | ------------------- |
| MCP Gateway    | `9000` | MCP tools           |
| Flight Agent   | `8001` | Flight processing   |
| Hotel Agent    | `8002` | Hotel processing    |
| Router Agent   | `8003` | Agent orchestration |
| Travel Gateway | `8000` | Main travel API     |

---

# Project Structure

```
a2a-travel-demo/
│
├── .env
├── requirements.txt
├── run_all.py
│
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   └── models.py
│
├── mcp_gateway/
│   ├── __init__.py
│   └── main.py
│
├── agents/
│   ├── __init__.py
│   │
│   ├── flight_agent/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── hotel_agent/
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   └── router_agent/
│       ├── __init__.py
│       └── main.py
│
├── gateway/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_mcp.py
│   ├── check_mcp_tools.py
│   └── test_agent.py
│
└── reports/
```

---

# Folder Responsibilities

 The important architectural separation is:

```
gateway/
    │
    └── External Travel API
```

```
agents/
    │
    ├── Flight Agent
    ├── Hotel Agent
    └── Router Agent
```

```
mcp_gateway/
    │
    └── Central MCP Tool Gateway
```

```
common/
    │
    ├── Shared configuration
    ├── LLM configuration
    └── Pydantic contracts
```

```
tests/
    │
    ├── MCP tests
    └── End-to-end agent tests
```

---

# Pydantic Shared Contracts

 The `common/models.py` file contains shared Pydantic models.

 These models define the contracts between the components.

 For example:

```
AgentRequest
     │
     ▼
Agent
     │
     ▼
FlightAgentResult
     │
     ▼
Travel Gateway
```

 This keeps communication structured and predictable.

 Instead of passing arbitrary dictionaries between agents, the application uses defined Pydantic response models.

---

# Groq + Structured Output

 The agents use the Groq LLM for recommendation and reasoning.

 The LLM is configured through:

```
common/llm.py
```

 The API key and model are configured using `.env`.

 Example:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

 The agents use structured output so that the LLM response conforms to the corresponding Pydantic model.

 For example:

```
LLM
 │
 ▼
FlightAgentResult
```

 or:

```
LLM
 │
 ▼
HotelAgentResult
```

 The LLM is instructed to use only the data returned by the MCP tools.

---

# LangGraph

 The Router Agent uses LangGraph to orchestrate the workflow.

 Conceptually:

```
                    START
                      │
                      ▼
                Analyze Request
                      │
              ┌───────┴───────┐
              │               │
              ▼               ▼
        Flight Needed?   Hotel Needed?
              │               │
              ▼               ▼
        Flight Agent     Hotel Agent
              │               │
              └───────┬───────┘
                      │
                      ▼
              Combine Results
                      │
                      ▼
                Travel Plan
                      │
                      ▼
                     END
```

 This allows the Router Agent to coordinate multiple specialist agents instead of placing all travel logic in a single application.

---

# Agent Cards

 Each A2A agent can expose an Agent Card at:

```
/.well-known/agent-card.json
```

### Flight Agent

```
http://127.0.0.1:8001/.well-known/agent-card.json
```

 Example:

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

### Hotel Agent

```
http://127.0.0.1:8002/.well-known/agent-card.json
```

### Router Agent

```
http://127.0.0.1:8003/.well-known/agent-card.json
```

 The conceptual difference is:

```
Agent Card
    |
    +--> Identity
    +--> URL
    +--> Capabilities
    +--> Skills
```

 while MCP provides:

```
MCP
 |
 +--> Tools
 +--> Tool Schemas
 +--> Tool Execution
```

---

# Installation

## 1\. Create the Environment

 Using Conda:

```
conda create --prefix ./venv python=3.14 -y
```

 Activate the environment:

```
conda activate ./venv
```

---

## 2\. Install Dependencies

 Install the project dependencies:

```
pip install -r requirements.txt
```

---

# Environment Variables

 Create a `.env` file in the project root.

 Example:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

 Replace:

```
your_groq_api_key_here
```

 with your actual Groq API key.

 Do not commit `.env` or API keys to source control.

---

# Running the Application

 There are two ways to run the application.

## Option 1 — Run Manually

 The MCP Gateway should be started separately.

### Terminal 1 — MCP Gateway

```
python mcp_gateway\main.py
```

 The MCP server runs at:

```
http://127.0.0.1:9000/mcp
```

### Test MCP

 Open another terminal:

```
python tests/test_mcp.py
```

 You can also check the available tools:

```
python -m tests.check_mcp_tools
```

 Expected tools:

```
search_flights
flight_price
search_hotels
hotel_price
```

---

### Terminal 2 — Flight Agent

```
uvicorn agents.flight_agent.main:app --host 127.0.0.1 --port 8001
```

 Test it:

```
curl -X POST http://127.0.0.1:8001/ ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Find me a flight to Goa\"}"
```

---

### Terminal 3 — Hotel Agent

```
uvicorn agents.hotel_agent.main:app --host 127.0.0.1 --port 8002
```

---

### Terminal 4 — Router Agent

```
uvicorn agents.router_agent.main:app --host 127.0.0.1 --port 8003
```

 Open Swagger:

```
http://127.0.0.1:8003/docs
```

---

### Terminal 5 — Travel Gateway

```
uvicorn gateway.main:app --host 127.0.0.1 --port 8000
```

 The main API is now available at:

```
http://127.0.0.1:8000
```

---

### Terminal 6 — End-to-End Test

 Run:

```
python tests\test_agent.py
```

 This sends requests through the complete system.

---

# Option 2 — Run Everything Automatically

 The project includes:

```
run_all.py
```

 The MCP Gateway is intentionally kept separate.

 Start the MCP Gateway first:

```
python mcp_gateway\main.py
```

 Then, from another terminal, start the remaining services:

```
python run_all.py
```

 `run_all.py` starts:

```
Flight Agent     :8001
Hotel Agent      :8002
Router Agent     :8003
Travel Gateway   :8000
```

 It does **not** start:

```
MCP Gateway      :9000
```

 because the MCP Gateway is started separately.

 After everything is running:

```
python tests/test_agent.py
```

---

# Testing Strategy

 The recommended testing approach is to test the system layer by layer.

## 1\. Test MCP

```
python tests/test_mcp.py
```

 This verifies:

```
MCP Connection
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

## 2\. Test MCP Tool Discovery

```
python -m tests.check_mcp_tools
```

 This confirms that the MCP Gateway exposes the expected tools.

---

## 3\. Test Individual Agent

 For example, test the Flight Agent:

```
curl -X POST http://127.0.0.1:8001/ ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Find me a flight to Goa\"}"
```

---

## 4\. Test Router

 Open:

```
http://127.0.0.1:8003/docs
```

 Use the Swagger UI to test Router Agent endpoints.

---

## 5\. Test Complete System

 Run:

```
python tests\test_agent.py
```

 This performs the end-to-end test:

```
Test Client
     │
     ▼
Travel Gateway
     │
     ▼
Router Agent
     │
     ├────────► Flight Agent
     │              │
     │              ▼
     │         MCP Gateway
     │
     └────────► Hotel Agent
                    │
                    ▼
               MCP Gateway
                    │
                    ▼
               Travel Plan
```

---

# Example End-to-End Request

 The test client can send:

```
Plan a 3 day trip to Goa.
Find me a flight and hotel.
```

 The complete flow is:

```
1. Test Client
       │
       ▼
2. POST /plan
       │
       ▼
3. Travel Gateway :8000
       │
       ▼
4. Router Agent :8003
       │
       ├─────────────────┐
       ▼                 ▼
5. Flight Agent     6. Hotel Agent
       │                 │
       ▼                 ▼
7. MCP Gateway      8. MCP Gateway
       │                 │
       ▼                 ▼
search_flights     search_hotels
       │                 │
       ▼                 ▼
Flight Result       Hotel Result
       │                 │
       └────────┬────────┘
                ▼
       9. Router combines results
                │
                ▼
       10. Travel Plan
                │
                ▼
       11. Travel Gateway
                │
                ▼
       12. Test Client
```

---

# Final Architecture

 The complete POC can be understood as four layers:

```
┌───────────────────────────────────────────────┐
│              CLIENT / TESTING                │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│              TRAVEL GATEWAY                   │
│                  :8000                        │
│              POST /plan                       │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                ROUTER AGENT                   │
│                  :8003                        │
│              LangGraph                        │
└───────────────────────┬───────────────────────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
┌─────────────────────┐  ┌─────────────────────┐
│   FLIGHT AGENT      │  │    HOTEL AGENT      │
│       :8001         │  │        :8002        │
│       A2A           │  │        A2A          │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           │         MCP            │
           └───────────┬────────────┘
                       ▼
┌───────────────────────────────────────────────┐
│                 MCP GATEWAY                   │
│                    :9000                      │
│                                               │
│  search_flights   flight_price                │
│  search_hotels    hotel_price                 │
└───────────────────────────────────────────────┘
```

---

# Key Takeaway

 This POC separates the responsibilities clearly:

```
FastAPI
   │
   └── HTTP service boundary

A2A
   │
   └── Agent-to-Agent communication

LangGraph
   │
   └── Agent workflow orchestration

MCP
   │
   └── Tool discovery and execution

Groq
   │
   └── LLM reasoning and recommendations

Pydantic
   │
   └── Structured contracts

Tests
   │
   └── MCP + Agent + End-to-End validation
```

 The most important architectural idea is:

```
                A2A
                 │
       Agent  ◄──┼──► Agent
                 │
                 ▼
                MCP
                 │
                 ▼
               Tools
```

 **A2A connects agents. MCP connects agents to tools. LangGraph orchestrates the agent workflow, while Groq provides the LLM reasoning and Pydantic keeps the data structured.**
