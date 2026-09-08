from fastapi import FastAPI
from fastmcp import Client

from common.config import MCP_GATEWAY_URL
from common.llm import get_llm
from common.models import (
    AgentCard,
    AgentRequest,
    Flight,
    FlightAgentResult,
)

app = FastAPI(title="Flight Agent")

llm = get_llm()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "flight-agent",
        "mcp_gateway": MCP_GATEWAY_URL,
    }


# ============================================================
# AGENT CARD
# ============================================================

@app.get("/.well-known/agent-card.json", response_model=AgentCard)
async def agent_card():

    return AgentCard(
        name="flight-agent",
        description="Finds flights for travel destinations",
        url="http://127.0.0.1:8001",
        skills=[
            "flight_search",
            "flight_price",
        ],
    )


# ============================================================
# MCP FLIGHT TOOL
# ============================================================

async def call_mcp_flight_tool(destination: str) -> list[dict]:

    async with Client(MCP_GATEWAY_URL) as client:

        # MCP server exposes:
        #
        # search_flights
        #
        # Therefore the tool name must match exactly.

        result = await client.call_tool(
            "search_flights",
            {
                "destination": destination,
            },
        )

        return result.data


# ============================================================
# FLIGHT AGENT
# ============================================================

@app.post("/", response_model=FlightAgentResult)
async def handle_request(request: AgentRequest):

    # --------------------------------------------------------
    # Determine destination
    # --------------------------------------------------------

    destination = "goa"

    message = request.message.lower()

    if "mumbai" in message:
        destination = "mumbai"

    # --------------------------------------------------------
    # Call MCP
    # --------------------------------------------------------

    raw_flights = await call_mcp_flight_tool(destination)

    # --------------------------------------------------------
    # Convert MCP response to Flight models
    # --------------------------------------------------------

    flights = [
        Flight(**flight)
        for flight in raw_flights
    ]

    # --------------------------------------------------------
    # No flights found
    # --------------------------------------------------------

    if not flights:

        return FlightAgentResult(
            agent="flight-agent",
            destination=destination,
            flights=[],
            recommendation="No flights found.",
            tools_called=["search_flights"],
        )

    # --------------------------------------------------------
    # Ask LLM to recommend
    # --------------------------------------------------------

    llm_with_structure = llm.with_structured_output(
        FlightAgentResult
    )

    result = await llm_with_structure.ainvoke(
        f"""
            You are the Flight Agent.

            User request:
            {request.message}

            Available flights:
            {[flight.model_dump() for flight in flights]}

            Recommend the best flight.

            Rules:
            - Do not invent flights.
            - Use only the supplied flight data.
            - Keep the recommendation short.
            - Return destination, flights and recommendation.
        """
    )

    # --------------------------------------------------------
    # Add agent/tool metadata
    # --------------------------------------------------------

    result.agent = "flight-agent"
    result.tools_called = ["search_flights"]

    return result
