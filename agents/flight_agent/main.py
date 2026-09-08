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

@app.get("/.well-known/agent-card.json", response_model=AgentCard)
async def agent_card():

    return AgentCard(
        name="flight-agent",
        description="Finds flights for travel destinations",
        url="http://127.0.0.1:8001",
        skills=["flight_search", "flight_price",]
    )

async def call_mcp_flight_tool(destination: str) -> list[dict]:
    async with Client(MCP_GATEWAY_URL) as client:

        result = await client.call_tool(
            "search_flights",
            {
                "destination": destination,
            },
        )

        return result.data


@app.post("/", response_model=FlightAgentResult)
async def handle_request(request: AgentRequest):
    destination = "goa"

    if "mumbai" in request.message.lower():
        destination = "mumbai"

    raw_flights = await call_mcp_flight_tool(destination)

    flights = [Flight(**flight) for flight in raw_flights]

    if not flights:
        return FlightAgentResult(
            destination=destination,
            flights=[],
            recommendation="No flights found.",
            tools_called=["search_flights"],
        )

    llm_with_structure = llm.with_structured_output(FlightAgentResult)
    result = llm_with_structure.invoke(
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

    result.agent = "flight-agent"
    result.tools_called = ["search_flights"]

    return result