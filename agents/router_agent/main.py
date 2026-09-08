import asyncio

import httpx

from fastapi import FastAPI

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from typing_extensions import TypedDict

from common.config import (
    FLIGHT_AGENT_URL,
    HOTEL_AGENT_URL,
)

from common.llm import get_llm

from common.models import (
    AgentRequest,
    FlightAgentResult,
    HotelAgentResult,
    RouterDecision,
    TravelPlan,
)


app = FastAPI(
    title="Travel Router Agent",
    version="1.0.0",
)

llm = get_llm()


# ============================================================
# STATE
# ============================================================

class TravelState(TypedDict, total=False):

    message: str

    router_decision: RouterDecision

    flight_result: FlightAgentResult | None

    hotel_result: HotelAgentResult | None

    travel_plan: TravelPlan


# ============================================================
# ROUTE REQUEST
# ============================================================

def route_request(
    state: TravelState,
):

    structured_llm = llm.with_structured_output(
        RouterDecision
    )

    decision = structured_llm.invoke(
        f"""
You are the Router Agent for a travel planning system.

User request:

{state["message"]}

Determine:

- destination
- whether a flight is needed
- whether a hotel is needed

For example:

"Plan a 3 day trip to Goa. Find me a flight and hotel."

should produce:

destination = Goa
needs_flight = true
needs_hotel = true

Do not invent information.
"""
    )

    return {
        "router_decision": decision
    }


# ============================================================
# CALL FLIGHT AGENT
# ============================================================

async def call_flight_agent(
    message: str,
):

    async with httpx.AsyncClient(
        timeout=60
    ) as client:

        response = await client.post(
            f"{FLIGHT_AGENT_URL}/",
            json={
                "message": message
            },
        )

        response.raise_for_status()

        return FlightAgentResult.model_validate(
            response.json()
        )


# ============================================================
# CALL HOTEL AGENT
# ============================================================

async def call_hotel_agent(
    message: str,
):

    async with httpx.AsyncClient(
        timeout=60
    ) as client:

        response = await client.post(
            f"{HOTEL_AGENT_URL}/",
            json={
                "message": message
            },
        )

        response.raise_for_status()

        return HotelAgentResult.model_validate(
            response.json()
        )


# ============================================================
# CALL AGENTS
# ============================================================

async def call_agents(
    state: TravelState,
):

    decision = state["router_decision"]

    tasks = []

    if decision.needs_flight:

        tasks.append(
            call_flight_agent(
                state["message"]
            )
        )

    else:

        tasks.append(
            asyncio.sleep(
                0,
                result=None,
            )
        )

    if decision.needs_hotel:

        tasks.append(
            call_hotel_agent(
                state["message"]
            )
        )

    else:

        tasks.append(
            asyncio.sleep(
                0,
                result=None,
            )
        )

    flight_result, hotel_result = (
        await asyncio.gather(*tasks)
    )

    return {
        "flight_result": flight_result,
        "hotel_result": hotel_result,
    }


# ============================================================
# BUILD PLAN
# ============================================================

def build_plan(
    state: TravelState,
):

    decision = state["router_decision"]

    flight_result = state.get(
        "flight_result"
    )

    hotel_result = state.get(
        "hotel_result"
    )

    selected_flight = None
    selected_hotel = None

    flight_cost = 0.0
    hotel_cost = 0.0

    duration_days = 3

    # --------------------------------------------------------
    # SELECT FLIGHT
    # --------------------------------------------------------

    if (
        flight_result
        and flight_result.flights
    ):

        selected_flight = min(
            flight_result.flights,
            key=lambda flight: flight.price,
        )

        flight_cost = selected_flight.price

    # --------------------------------------------------------
    # SELECT HOTEL
    # --------------------------------------------------------

    if (
        hotel_result
        and hotel_result.hotels
    ):

        selected_hotel = max(
            hotel_result.hotels,
            key=lambda hotel: hotel.rating,
        )

        hotel_cost = (
            selected_hotel.price_per_night
            * selected_hotel.nights
        )

    total = (
        flight_cost
        + hotel_cost
    )

    summary = (
        f"Recommended trip to "
        f"{decision.destination}. "
    )

    if selected_flight:

        summary += (
            f"Flight: "
            f"{selected_flight.airline} "
            f"{selected_flight.flight}. "
        )

    if selected_hotel:

        summary += (
            f"Hotel: "
            f"{selected_hotel.name}. "
        )

    summary += (
        f"Estimated total cost: "
        f"₹{total:.2f}."
    )

    return {
        "travel_plan": TravelPlan(
            destination=decision.destination,
            duration_days=duration_days,
            selected_flight=selected_flight,
            selected_hotel=selected_hotel,
            estimated_flight_cost=flight_cost,
            estimated_hotel_cost=hotel_cost,
            estimated_total_cost=total,
            summary=summary,
        )
    }


# ============================================================
# LANGGRAPH
# ============================================================

builder = StateGraph(
    TravelState
)

builder.add_node(
    "route_request",
    route_request,
)

builder.add_node(
    "call_agents",
    call_agents,
)

builder.add_node(
    "build_plan",
    build_plan,
)


builder.add_edge(
    START,
    "route_request",
)

builder.add_edge(
    "route_request",
    "call_agents",
)

builder.add_edge(
    "call_agents",
    "build_plan",
)

builder.add_edge(
    "build_plan",
    END,
)


travel_graph = builder.compile()


# ============================================================
# API
# ============================================================

@app.get("/")
async def health():

    return {
        "status": "ok",
        "agent": "travel-router-agent",
        "orchestration": "langgraph",
    }


@app.post("/")
async def travel(
    request: AgentRequest,
):

    result = await travel_graph.ainvoke(
        {
            "message": request.message
        }
    )

    decision = result[
        "router_decision"
    ]

    flight_result = result.get(
        "flight_result"
    )

    hotel_result = result.get(
        "hotel_result"
    )

    return {
        "agent": "travel-router-agent",

        "destination": (
            decision.destination
        ),

        "decision": (
            decision.model_dump()
        ),

        "flight_agent": (
            flight_result.model_dump()
            if flight_result
            else None
        ),

        "hotel_agent": (
            hotel_result.model_dump()
            if hotel_result
            else None
        ),

        "travel_plan": (
            result["travel_plan"]
            .model_dump()
        ),
    }
