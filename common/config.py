import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured. Set it in .env")


FLIGHT_AGENT_URL = "http://127.0.0.1:8001"
HOTEL_AGENT_URL = "http://127.0.0.1:8002"

MCP_GATEWAY_URL = "http://127.0.0.1:9000/mcp"

ROUTER_AGENT_URL = "http://127.0.0.1:8003"
