import time

import httpx
from fastapi import FastAPI, HTTPException

from common.config import ROUTER_AGENT_URL
from common.models import AgentRequest


app = FastAPI(
    title="Travel Gateway",
    version="1.0.0",
)


@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "travel-gateway",
        "router_agent": ROUTER_AGENT_URL,
    }


@app.post("/plan")
async def plan_trip(request: AgentRequest):

    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(
            timeout=120
        ) as client:

            response = await client.post(
                f"{ROUTER_AGENT_URL}/",
                json=request.model_dump(),
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Router Agent unavailable: {exc}",
        )

    latency_ms = int(
        (time.perf_counter() - started) * 1000
    )

    data = response.json()

    flight_agent = data.get("flight_agent")
    hotel_agent = data.get("hotel_agent")

    agents_called = []
    tools_called = []

    if flight_agent:
        agents_called.append("flight-agent")
        tools_called.extend(
            flight_agent.get("tools_called", [])
        )

    if hotel_agent:
        agents_called.append("hotel-agent")
        tools_called.extend(
            hotel_agent.get("tools_called", [])
        )

    return {
        "status": "completed",
        "latency_ms": latency_ms,
        "destination": data.get("destination"),
        "duration_days": (
            data.get("travel_plan", {})
            .get("duration_days")
        ),
        "travel_plan": data.get("travel_plan"),
        "agents_called": agents_called,
        "tools_called": tools_called,
    }
