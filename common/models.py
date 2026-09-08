from typing import Literal
from pydantic import BaseModel, Field

# ============================================================
# Generic A2A
# ============================================================

class AgentRequest(BaseModel):
    message: str


class AgentCard(BaseModel):
    name : str
    description : str 
    url : str
    skills : list[str]


# ============================================================
# Flight
# ============================================================

class Flight(BaseModel):
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price_usd: float

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str

class FlightAgentResponse(BaseModel):
    agent: str = "flight-agent"
    status: Literal["completed", "failed"]
    destination: str
    flights: list[Flight]
    recommendation: str
    tools_called: list[str]


# ============================================================
# Hotel
# ============================================================

class Hotel(BaseModel):
    name: str
    city: str
    price_per_night_usd: float
    rating: float
    amenities: list[str]

class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str

class HotelAgentResponse(BaseModel):
    agent: str = "hotel-agent"
    status: Literal["completed", "failed"]
    destination: str
    hotels: list[Hotel]
    recommendation: str
    tools_called: list[str]


# ============================================================
# Router
# ============================================================

class RouteDecision(BaseModel):
    destination: str
    origin: str
    departure_date: str
    check_in: str
    check_out: str
    needs_flight: bool
    needs_hotel: bool


# ============================================================
# Final Travel Plan
# ============================================================

class TravelPlan(BaseModel):
    destination: str
    trip_summary: str
    flight: FlightAgentResponse | None
    hotel: HotelAgentResponse | None
    recommendation: str

# ============================================================
# Router response
# ============================================================

class RouterAgentResponse(BaseModel):
    agent: str = "router-agent"
    status: Literal["completed", "failed"]
    plan: TravelPlan
    tools_called: list[str]
    agents_called: list[str]


# ============================================================
# Gateway
# ============================================================

class TravelResponse(BaseModel):
    status: Literal["completed", "failed"]
    latency_ms: int
    agent_response: RouterAgentResponse

