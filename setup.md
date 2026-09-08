This gives you A2A + Router Agent + LangGraph + MCP + tools + Groq + structured Pydantic responses, while still being small enough to understand.

a Travel Agent POC that demonstrates all four concepts independently and together:

A2A — Router Agent ↔ Flight Agent / Hotel Agent
MCP — agents consume tools from a central FastMCP Gateway
LangGraph — Router Agent orchestrates the workflow
Groq — LLM reasoning + structured output
Pydantic — shared contracts under common/
FastAPI — HTTP service boundary for each A2A agent
Testing — one end-to-end test client
run_all.py — starts every service
Structured console output matching your requested format


                              USER
                                |
                                v
                    +-----------------------+
                    |    TRAVEL GATEWAY     |
                    |       FastAPI         |
                    |        :8000          |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |     ROUTER AGENT      |
                    |       LangGraph       |
                    |        + Groq         |
                    +-----------+-----------+
                                |
                 +--------------+--------------+
                 |                             |
                 v                             v
       +-------------------+          +-------------------+
       |   FLIGHT AGENT    |          |    HOTEL AGENT    |
       |     FastAPI       |          |      FastAPI      |
       |      :8001        |          |       :8002       |
       +---------+---------+          +---------+---------+
                 |                              |
                 | A2A HTTP                     | A2A HTTP
                 |                              |
                 +--------------+---------------+
                                |
                                v
                  +-----------------------------+
                  |       MCP GATEWAY           |
                  |          FastMCP             |
                  |           :9000              |
                  |                             |
                  |  search_flights              |
                  |  search_hotels               |
                  |  flight_price                 |
                  |  hotel_price                 |
                  +--------------+--------------+
                                 |
                    +------------+------------+
                    |                         |
                    v                         v
             Flight mock DB              Hotel mock DB


There are two different communication patterns here:
A2A
Router Agent
    |
    | HTTP POST
    v
Flight Agent

and 
Router Agent
    |
    | HTTP POST
    v
Hotel Agent

MCP 

Flight Agent
     |
     | MCP / Streamable HTTP
     v
MCP Gateway
     |
     v
search_flights()

Hotel Agent
     |
     | MCP / Streamable HTTP
     v
MCP Gateway
     |
     v
search_hotels()

This separation is important.

A2A answers:

"Which agent should I communicate with?"

MCP answers:

"Which tools/resources can this agent use?"


Folder Structure

a2a-mcp-travel/
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
│   └── test_agent.py
│
└── reports/

The important architectural distinction is:

gateway/
    = external Travel API

agents/
    = A2A agents

mcp_gateway/
    = tool gateway

common/
    = contracts/shared infrastructure




GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b

```
conda create --prefix ./venv python=3.14 -y
conda activate ./venv 
pip install -r requirements.txt
```
