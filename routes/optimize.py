from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict
from services.mapbox_service import MapboxService
from services.texas_toll_service import TexasTollService
from services.routing_optimizer import RoutingOptimizer
from models.route import RoutePreferences
import os
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()


class OptimizeRequest(BaseModel):
    origin: Dict[str, float]  # {"lat": float, "lng": float}
    destination: Dict[str, float]
    preferences: Optional[RoutePreferences] = None
    has_toll_tag: Optional[bool] = True  # Whether vehicle has TxTag/EZ Tag
    
    @field_validator('origin', 'destination')
    @classmethod
    def validate_coordinates(cls, v: Dict[str, float]) -> Dict[str, float]:
        if 'lat' not in v or 'lng' not in v:
            raise ValueError('Coordinates must have lat and lng fields')
        
        lat, lng = v['lat'], v['lng']
        
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            raise ValueError('Latitude and longitude must be numbers')
        
        if not (-90 <= lat <= 90):
            raise ValueError(f'Latitude must be between -90 and 90, got {lat}')
        
        if not (-180 <= lng <= 180):
            raise ValueError(f'Longitude must be between -180 and 180, got {lng}')
        
        return v


class OptimizeResponse(BaseModel):
    budget_usd: float
    no_toll_option: Dict
    budget_option: Dict
    alternatives: List[Dict]
    advisories: List[str]


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_routes(request: OptimizeRequest):
    """
    Optimize route selection based on toll budget constraint
    
    Returns fastest route within user's toll budget
    
    - **origin**: Starting location coordinates
    - **destination**: Destination coordinates
    - **preferences**: Routing preferences including toll_budget_usd
    """
    start_time = time.time()
    logger.info(f"Route optimization request: {request.origin} -> {request.destination}")
    
    try:
        # Initialize services
        mapbox_token = os.getenv("MAPBOX_ACCESS_TOKEN")
        if not mapbox_token or mapbox_token == "pk.your_mapbox_token_here":
            logger.error("Mapbox API token not configured or still using placeholder")
            raise HTTPException(
                status_code=500,
                detail="Mapbox API token not configured. Please set MAPBOX_ACCESS_TOKEN in .env file."
            )
        
        mapbox_service = MapboxService(access_token=mapbox_token)
        has_tag = request.has_toll_tag if request.has_toll_tag is not None else True
        toll_service = TexasTollService(has_toll_tag=has_tag)  # Texas-wide toll pricing
        optimizer = RoutingOptimizer()
        
        # Get route candidates from Mapbox (regular routes with alternatives)
        preferences_dict = request.preferences.model_dump() if request.preferences else {}
        candidates = await mapbox_service.get_route_candidates(
            request.origin,
            request.destination,
            preferences_dict
        )
        
        # Also get a toll-free route explicitly (I-35 only in Austin)
        toll_free_prefs = preferences_dict.copy()
        toll_free_prefs["avoid_tolls"] = True
        try:
            toll_free_candidates = await mapbox_service.get_route_candidates(
                request.origin,
                request.destination,
                toll_free_prefs
            )
            # Add toll-free routes if they're different from existing candidates
            for toll_free_route in toll_free_candidates:
                # Check if this route is unique (different distance)
                is_unique = True
                for existing in candidates:
                    if abs(existing.distance_meters - toll_free_route.distance_meters) < 1000:  # Within 1km
                        is_unique = False
                        break
                if is_unique:
                    candidates.append(toll_free_route)
        except Exception as e:
            logger.warning(f"Could not fetch toll-free route: {e}")
        
        if not candidates:
            logger.warning(f"No routes found for {request.origin} -> {request.destination}")
            raise HTTPException(
                status_code=404,
                detail="No routes found for given origin and destination. Check coordinates validity."
            )
        
        # Estimate toll costs
        candidates_with_tolls = toll_service.estimate_tolls(candidates)
        
        # Apply budget optimization
        budget = preferences_dict.get("toll_budget_usd", 10.0)  # Default $10
        result = optimizer.optimize_routes(candidates_with_tolls, budget)
        
        elapsed_time = time.time() - start_time
        total_routes = 2 + len(result.get('alternatives', []))  # no_toll + budget + alternatives
        logger.info(f"Route optimization completed in {elapsed_time:.2f}s, {total_routes} routes")
        
        return OptimizeResponse(**result)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except ConnectionError as e:
        logger.error(f"Mapbox API connection error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Unable to reach routing service. Please try again later."
        )
    except TimeoutError as e:
        logger.error(f"Mapbox API timeout: {str(e)}")
        raise HTTPException(
            status_code=504,
            detail="Routing service timed out. Please try again."
        )
    except Exception as e:
        logger.exception(f"Unexpected error in route optimization: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Route optimization failed: {type(e).__name__}. Check server logs for details."
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for routing service"""
    return {"status": "healthy", "service": "routing"}
