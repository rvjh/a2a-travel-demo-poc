This gives you A2A + Router Agent + LangGraph + MCP + tools + Groq + structured Pydantic responses, while still being small enough to understand.


                         USER
                           |
                           v
                 +-------------------+
                 |   Travel Gateway   |
                 |      :8000         |
                 +---------+---------+
                           |
                           | A2A / HTTP
                           v
                 +-------------------+
                 |    Router Agent    |
                 |      :8003         |
                 |    LangGraph       |
                 +----+---------+-----+
                      |         |
                 A2A  |         |  A2A
                      v         v
              +-----------+ +-----------+
              |  Flight   | |   Hotel   |
              |   Agent   | |   Agent   |
              |   :8001   | |   :8002   |
              +-----+-----+ +-----+-----+
                    |             |
                    | MCP        | MCP
                    +------+------+
                           v
                 +-------------------+
                 |    MCP Gateway    |
                 |      :9000        |
                 |  Streamable HTTP  |
                 +---------+---------+
                           |
                    +------+------+
                    |             |
                    v             v
              flight_search   hotel_search




Folder Structure

a2a-travel-poc/
│
├── common/
│   ├── __init__.py
│   ├── llm_client.py
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
│       ├── graph.py
│       └── main.py
│
├── gateway/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   └── client.py
│
├── reports/
│
├── .env
├── requirements.txt
└── run_all.py


GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b


```
conda create --prefix ./venv python=3.14 -y
conda activate ./venv 
pip install -r requirements.txt

```


