import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured. Set it in .env")


# ============================================================
# URLs  - Uncomment While running locally
# ============================================================

# FLIGHT_AGENT_URL = "http://127.0.0.1:8001"
# HOTEL_AGENT_URL = "http://127.0.0.1:8002"

# MCP_GATEWAY_URL = "http://127.0.0.1:9000/mcp"

# ROUTER_AGENT_URL = "http://127.0.0.1:8003"



# ============================================================
# SERVICE URLs  - Uncomment While running with docker
# ============================================================
#
# These hostnames are Docker Compose service names.
# Containers communicate with each other using these names.
#

FLIGHT_AGENT_URL = os.getenv(
    "FLIGHT_AGENT_URL",
    "http://flight-agent:8001",
)

HOTEL_AGENT_URL = os.getenv(
    "HOTEL_AGENT_URL",
    "http://hotel-agent:8002",
)

ROUTER_AGENT_URL = os.getenv(
    "ROUTER_AGENT_URL",
    "http://router-agent:8003",
)

MCP_GATEWAY_URL = os.getenv(
    "MCP_GATEWAY_URL",
    "http://mcp-gateway:9000/mcp",
)