import asyncio
import httpx
from fastapi import FastAPI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from typing_extensions import TypedDict

from common.config import FLIGHT_AGENT_URL, HOTEL_AGENT_URL
from common.llm import get_llm
from common.models import AgentRequest, FlightAgentResult, HotelAgentResult, RouterDecision, TravelPlan

app = FastAPI(title="Travel Router Agent")

llm = get_llm()


# ============================================================
# LANGGRAPH STATE
# ============================================================

class TravelState(TypedDict, total=False):
    message: str
    router_decision: RouterDecision
    flight_result: FlightAgentResult | None
    hotel_result: HotelAgentResult | None
    travel_plan: TravelPlan

# ============================================================
# ROUTER NODE
# ============================================================

def route_request(state: TravelState):
    structured_llm = llm.with_structured_output(RouterDecision)
    decision = structured_llm.invoke(
        f"""
            You are the Router Agent for a travel planning system.

            User request:
            {state["message"]}

            Determine:

            1. destination
            2. whether a flight is required
            3. whether a hotel is required

            This is a travel planning request.

            Examples:

            "Find me a flight to Goa"
            => needs_flight=true
            => needs_hotel=false

            "Find me a hotel in Goa"
            => needs_flight=false
            => needs_hotel=true

            "Plan a 3 day trip to Goa. Find a flight and hotel."
            => needs_flight=true
            => needs_hotel=true

            Do not invent destinations.
            """
    )

    return {"router_decision": decision}


# ============================================================
# A2A CALLS
# ============================================================

async def call_flight_agent(message: str) -> FlightAgentResult:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{FLIGHT_AGENT_URL}/",json={"message": message})

        response.raise_for_status()

        return FlightAgentResult.model_validate(response.json())


async def call_hotel_agent(message: str) -> HotelAgentResult:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{HOTEL_AGENT_URL}/", json={"message": message})

        response.raise_for_status()

        return HotelAgentResult.model_validate(response.json())


# ============================================================
# FLIGHT NODE
# ============================================================

async def flight_node(state: TravelState):
    decision = state["router_decision"]

    if not decision.needs_flight:
        return {"flight_result": None}

    result = await call_flight_agent(state["message"])

    return {"flight_result": result}


# ============================================================
# HOTEL NODE
# ============================================================

async def hotel_node(state: TravelState):
    decision = state["router_decision"]

    if not decision.needs_hotel:
        return {"hotel_result": None}

    result = await call_hotel_agent(state["message"])

    return {"hotel_result": result}


# ============================================================
# BUILD FINAL PLAN
# ============================================================

def build_plan(state: TravelState):

    decision = state["router_decision"]

    flight_result = state.get("flight_result")

    hotel_result = state.get("hotel_result")

    selected_flight = None
    selected_hotel = None

    flight_cost = 0.0
    hotel_cost = 0.0

    duration_days = 3

    # --------------------------------------------------------
    # SELECT FLIGHT
    # --------------------------------------------------------

    if (flight_result and flight_result.flights):

        selected_flight = min(flight_result.flights, key=lambda x: x.price)
        flight_cost = selected_flight.price

    # --------------------------------------------------------
    # SELECT HOTEL
    # --------------------------------------------------------

    if (hotel_result and hotel_result.hotels):

        selected_hotel = max(hotel_result.hotels, key=lambda x: x.rating)

        hotel_cost = (selected_hotel.price_per_night * selected_hotel.nights)

    total = flight_cost + hotel_cost

    summary_parts = []

    if selected_flight:

        summary_parts.append(
            f"Flight: "
            f"{selected_flight.airline} "
            f"{selected_flight.flight}"
        )

    if selected_hotel:

        summary_parts.append(
            f"Hotel: "
            f"{selected_hotel.name}"
        )

    summary = (
        f"Recommended {decision.destination} trip. "
        + " | ".join(summary_parts)
        + f". Estimated total: ₹{total:.2f}."
    )

    plan = TravelPlan(
        destination=decision.destination,
        duration_days=duration_days,
        selected_flight=selected_flight,
        selected_hotel=selected_hotel,
        estimated_flight_cost=flight_cost,
        estimated_hotel_cost=hotel_cost,
        estimated_total_cost=total,
        summary=summary,
    )

    return {
        "travel_plan": plan
    }


# ============================================================
# LANGGRAPH
# ============================================================

builder = StateGraph(TravelState)

builder.add_node("route_request", route_request)
builder.add_node("flight_agent",flight_node)
builder.add_node("hotel_agent",hotel_node)
builder.add_node("build_plan",build_plan)

builder.add_edge(START, "route_request")
builder.add_edge("route_request", "flight_agent")
builder.add_edge("route_request","hotel_agent")
builder.add_edge("flight_agent", "build_plan")
builder.add_edge("hotel_agent", "build_plan")
builder.add_edge("build_plan", END)

travel_graph = builder.compile()


# ============================================================
# API
# ============================================================

@app.post("/")
async def travel(request: AgentRequest):
    result = await travel_graph.ainvoke(
        {
            "message": request.message
        }
    )

    decision = result["router_decision"]

    return {
        "agent": "travel-router-agent",
        "destination": decision.destination,
        "decision": decision.model_dump(),
        "flight_agent": (
            result["flight_result"].model_dump()
            if result.get("flight_result")
            else None
        ),
        "hotel_agent": (
            result["hotel_result"].model_dump()
            if result.get("hotel_result")
            else None
        ),
        "travel_plan": result[
            "travel_plan"
        ].model_dump(),
    }
