Here’s a shorter README focused on the **main Docker changes, files to modify, commands, and architecture**.

 Docker Deployment README

# A2A Travel POC — Docker Setup

 ## Architecture

```
                         ┌──────────────────────┐
                         │      Client/Test     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Travel Gateway     │
                         │      :8000           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Router Agent      │
                         │      :8003           │
                         └───────┬───────┬──────┘
                                 │       │
                    A2A/HTTP     │       │     A2A/HTTP
                                 ▼       ▼
                         ┌──────────┐ ┌──────────┐
                         │ Flight   │ │  Hotel   │
                         │ Agent    │ │  Agent   │
                         │  :8001   │ │  :8002   │
                         └────┬─────┘ └────┬─────┘
                              │             │
                              └──────┬──────┘
                                     │
                                  MCP/HTTP
                                     ▼
                           ┌──────────────────┐
                           │   MCP Gateway    │
                           │      :9000       │
                           └──────────────────┘
```

 ### Communication

```
Client
  │
  ▼
Travel Gateway :8000
  │
  ▼
Router Agent :8003
  │
  ├──► Flight Agent :8001 ──► MCP Gateway :9000
  │
  └──► Hotel Agent :8002 ───► MCP Gateway :9000
```

---

 # 1\. Files to Change

 ## `common/config.py`

 Docker containers cannot use `127.0.0.1` to communicate with each other.

 Change:

```
FLIGHT_AGENT_URL = "http://127.0.0.1:8001"
HOTEL_AGENT_URL = "http://127.0.0.1:8002"
MCP_GATEWAY_URL = "http://127.0.0.1:9000/mcp"
ROUTER_AGENT_URL = "http://127.0.0.1:8003"
```

 to:

```
FLIGHT_AGENT_URL = os.getenv(
    "FLIGHT_AGENT_URL",
    "http://flight-agent:8001"
)

HOTEL_AGENT_URL = os.getenv(
    "HOTEL_AGENT_URL",
    "http://hotel-agent:8002"
)

MCP_GATEWAY_URL = os.getenv(
    "MCP_GATEWAY_URL",
    "http://mcp-gateway:9000/mcp"
)

ROUTER_AGENT_URL = os.getenv(
    "ROUTER_AGENT_URL",
    "http://router-agent:8003"
)
```

---

 # 2\. Dockerfile

 Create:

```
Dockerfile
```

```
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

 # 3\. docker-compose.yml

 Create:

```
docker-compose.yml
```

```
services:

  mcp-gateway:
    build: .
    command: python mcp_gateway/main.py
    ports:
      - "9000:9000"

  flight-agent:
    build: .
    command: python -m uvicorn agents.flight_agent.main:app --host 0.0.0.0 --port 8001
    ports:
      - "8001:8001"
    depends_on:
      - mcp-gateway

  hotel-agent:
    build: .
    command: python -m uvicorn agents.hotel_agent.main:app --host 0.0.0.0 --port 8002
    ports:
      - "8002:8002"
    depends_on:
      - mcp-gateway

  router-agent:
    build: .
    command: python -m uvicorn agents.router_agent.main:app --host 0.0.0.0 --port 8003
    ports:
      - "8003:8003"
    depends_on:
      - flight-agent
      - hotel-agent

  travel-gateway:
    build: .
    command: python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    depends_on:
      - router-agent
```

 Docker Compose creates a network automatically, so services can reach each other using names such as:

```
mcp-gateway
flight-agent
hotel-agent
router-agent
travel-gateway
```

---

 # 4\. `.env`

 Keep your API key in `.env`:

```
GROQ_API_KEY=your_groq_api_key
```

 Do **not** put the API key directly in `Dockerfile` or source code.

 Add `.env` to `.gitignore`.

---

 # 5\. Build Containers

 From the project root:

```
docker compose build
```

---

 # 6\. Start Everything

```
docker compose up
```

 Or run in background:

```
docker compose up -d
```

 Check containers:

```
docker compose ps
```

---

 # 7\. Test

 Travel Gateway:

```
curl http://localhost:8000
```

 Flight Agent:

```
curl http://localhost:8001/health
```

 MCP Gateway:

```
curl http://localhost:9000
```

 Then run the existing test:

```
python -m tests.test_agent
```

---

 # 8\. Stop Everything

```
docker compose down
```

 To rebuild after code changes:

```
docker compose down
docker compose build
docker compose up
```

 ## Important Docker Difference

 ### Local

```
127.0.0.1:8001
127.0.0.1:8002
127.0.0.1:8003
127.0.0.1:9000
```

 ### Docker

```
flight-agent:8001
hotel-agent:8002
router-agent:8003
mcp-gateway:9000
```

 The key change is: **inside Docker, containers communicate using service names, not `127.0.0.1`.**

 This keeps your current A2A + MCP design intact; the main Docker-specific change is the service URLs and binding Uvicorn to `0.0.0.0`.