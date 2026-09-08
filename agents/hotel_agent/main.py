from fastapi import FastAPI
from fastmcp import Client

from common.config import MCP_GATEWAY_URL
from common.llm import get_llm
from common.models import (
    AgentCard,
    AgentRequest,
    Hotel,
    HotelAgentResult,
)


app = FastAPI(title="Hotel Agent")

llm = get_llm()


@app.get("/.well-known/agent-card.json", response_model=AgentCard)
async def agent_card():
    return AgentCard(
        name="hotel-agent",
        description="Finds hotels for travel destinations",
        url="http://127.0.0.1:8002",
        skills=["hotel_search","hotel_price"],
    )


async def call_mcp_hotel_tool(destination: str, nights: int) -> list[dict]:
    async with Client(MCP_GATEWAY_URL) as client:
        result = await client.call_tool(
            "search_hotels",
            {
                "destination": destination,
                "nights": nights,
            },
        )

        return result.data


@app.post("/", response_model=HotelAgentResult)
async def handle_request(request: AgentRequest):
    destination = "goa"

    if "mumbai" in request.message.lower():
        destination = "mumbai"

    nights = 2

    if "3 day" in request.message.lower():
        nights = 2

    raw_hotels = await call_mcp_hotel_tool(destination, nights)

    hotels = [Hotel(**hotel) for hotel in raw_hotels]

    if not hotels:
        return HotelAgentResult(
            destination=destination,
            hotels=[],
            recommendation="No hotels found.",
            tools_called=["search_hotels"],
        )

    llm_with_structure = llm.with_structured_output(HotelAgentResult)

    result = llm_with_structure.invoke(
        f"""
            You are the Hotel Agent.

            User request:
            {request.message}

            Available hotels:
            {[hotel.model_dump() for hotel in hotels]}

            Recommend the best hotel.

            Rules:
            - Do not invent hotels.
            - Use only supplied hotel data.
            - Consider rating and price.
            - Return structured output.
            """
    )

    result.agent = "hotel-agent"
    result.tools_called = ["search_hotels"]

    return result
