from pydantic import BaseModel
from typing import Optional


class Coordinates(BaseModel):
    lat: float
    lng: float


class RouteCandidate(BaseModel):
    route_id: str
    eta_seconds: int
    distance_meters: int
    toll_estimate_usd: Optional[float] = None
    polyline: str
    geometry: Optional[dict] = None


class RoutePreferences(BaseModel):
    avoid_tolls: bool = False
    avoid_highways: bool = False
    toll_budget_usd: Optional[float] = None
