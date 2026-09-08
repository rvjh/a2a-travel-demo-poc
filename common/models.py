from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# A2A REQUEST
# ============================================================

class AgentRequest(BaseModel):
    message: str


# ============================================================
# AGENT CARD
# ============================================================

class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    skills: list[str]


# ============================================================
# FLIGHTS
# ============================================================

class Flight(BaseModel):
    airline: str
    flight: str
    from_city: str
    to_city: str
    price: float
    currency: str = "USD"
    duration_hours: float


class FlightAgentResult(BaseModel):
    agent: str = "flight-agent"
    destination: str
    flights: list[Flight]
    recommendation: str
    tools_called: list[str] = Field(default_factory=list)


# ============================================================
# HOTELS
# ============================================================

class Hotel(BaseModel):
    name: str
    destination: str
    price_per_night: float
    currency: str = "USD"
    rating: float
    nights: int


class HotelAgentResult(BaseModel):
    agent: str = "hotel-agent"
    destination: str
    hotels: list[Hotel]
    recommendation: str
    tools_called: list[str] = Field(default_factory=list)


# ============================================================
# ROUTER
# ============================================================

class RouterDecision(BaseModel):
    destination: str
    needs_flight: bool
    needs_hotel: bool
    reasoning: str


# ============================================================
# TRAVEL PLAN
# ============================================================

class TravelPlan(BaseModel):
    destination: str
    duration_days: int

    selected_flight: Flight | None = None
    selected_hotel: Hotel | None = None

    estimated_flight_cost: float = 0
    estimated_hotel_cost: float = 0
    estimated_total_cost: float = 0

    summary: str


# ============================================================
# COMPLETE RESPONSE
# ============================================================

class TravelAgentResponse(BaseModel):
    status: Literal["completed", "failed"]
    destination: str | None = None
    duration_days: int | None = None

    travel_plan: TravelPlan | None = None

    agents_called: list[str] = Field(default_factory=list)
    tools_called: list[str] = Field(default_factory=list)

    message: str | None = None
