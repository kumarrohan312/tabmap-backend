import httpx
import os
from typing import List, Dict, Optional
from models.route import RouteCandidate, Coordinates
from dotenv import load_dotenv

load_dotenv()


class MapboxService:
    """Service for interacting with Mapbox Directions API"""
    
    BASE_URL = "https://api.mapbox.com/directions/v5/mapbox"
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("MAPBOX_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("Mapbox access token is required")
    
    async def get_route_candidates(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        preferences: Optional[Dict[str, any]] = None
    ) -> List[RouteCandidate]:
        """
        Retrieve route candidates from Mapbox Directions API
        
        Args:
            origin: {"lat": float, "lng": float}
            destination: {"lat": float, "lng": float}
            preferences: Optional routing preferences (avoid_tolls, avoid_highways)
        
        Returns:
            List of RouteCandidate objects
        """
        response = await self._fetch_directions(origin, destination, preferences)
        
        if response.get("code") != "Ok":
            raise Exception(f"Mapbox API error: {response.get('code')}")
        
        routes = response.get("routes", [])
        candidates = []
        
        for idx, route in enumerate(routes):
            # Build enhanced geometry with legs/steps for toll calculation
            geometry = {
                "type": "LineString",
                "coordinates": route.get("geometry", {}).get("coordinates", []),
                "legs": route.get("legs", [])  # Include legs with steps for road name detection
            }
            
            candidate = RouteCandidate(
                route_id=f"mapbox_route_{idx}",
                eta_seconds=int(route["duration"]),
                distance_meters=int(route["distance"]),
                polyline="",  # We're using geometry instead of polyline for GeoJSON
                geometry=geometry,  # Enhanced geometry with road segments
                toll_estimate_usd=None  # Will be populated by toll service
            )
            candidates.append(candidate)
        
        return candidates
    
    async def _fetch_directions(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        preferences: Optional[Dict[str, any]] = None
    ) -> Dict:
        """
        Internal method to fetch directions from Mapbox API
        
        Args:
            origin: Origin coordinates
            destination: Destination coordinates
            preferences: Routing preferences
        
        Returns:
            Raw API response
        """
        # Build coordinates string: lng,lat;lng,lat
        coordinates = f"{origin['lng']},{origin['lat']};{destination['lng']},{destination['lat']}"
        
        # Build URL
        profile = "driving-traffic"  # Use traffic-aware routing
        url = f"{self.BASE_URL}/{profile}/{coordinates}"
        
        # Build query parameters
        params = {
            "access_token": self.access_token,
            "alternatives": 3,  # Request up to 3 alternative routes (max allowed)
            "geometries": "geojson",
            "overview": "full",
            "steps": "true"
        }
        
        # Apply preferences
        if preferences:
            exclude_list = []
            if preferences.get("avoid_tolls"):
                exclude_list.append("toll")
            if preferences.get("avoid_highways"):
                exclude_list.append("motorway")
            if exclude_list:
                params["exclude"] = ",".join(exclude_list)
        
        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
