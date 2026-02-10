from typing import List
from models.route import RouteCandidate
import random


class TollService:
    """Service for estimating toll costs on routes"""
    
    def __init__(self, use_mock: bool = True, seed: int = None):
        """
        Initialize toll service
        
        Args:
            use_mock: Use mock toll pricing model (True for MVP)
            seed: Random seed for deterministic testing (None for production)
        """
        self.use_mock = use_mock
        self.random = random.Random(seed)
    
    def estimate_tolls(self, routes: List[RouteCandidate]) -> List[RouteCandidate]:
        """
        Estimate toll costs for each route
        
        Args:
            routes: List of route candidates without toll estimates
        
        Returns:
            List of routes with toll_estimate_usd populated
        """
        if self.use_mock:
            return self._mock_toll_estimates(routes)
        else:
            # Production: integrate with real toll data provider
            return self._real_toll_estimates(routes)
    
    def _mock_toll_estimates(self, routes: List[RouteCandidate]) -> List[RouteCandidate]:
        """
        Generate mock toll estimates for MVP
        
        Mock logic:
        - Base toll: $0.10 per km
        - Random variation: ±20%
        - Some routes can be toll-free
        """
        for route in routes:
            # If already has toll estimate, keep it
            if route.toll_estimate_usd is not None:
                continue
            
            distance_km = route.distance_meters / 1000
            
            # Simple mock: 30% chance of toll-free route
            if self.random.random() < 0.3:
                route.toll_estimate_usd = 0.0
            else:
                # Base rate: $0.10/km with ±20% variation
                base_toll = distance_km * 0.10
                variation = self.random.uniform(0.8, 1.2)
                route.toll_estimate_usd = round(base_toll * variation, 2)
        
        return routes
    
    def _real_toll_estimates(self, routes: List[RouteCandidate]) -> List[RouteCandidate]:
        """
        Estimate tolls using real toll data provider
        
        TODO: Integrate with toll pricing API
        """
        # Placeholder for production integration
        raise NotImplementedError("Real toll provider integration pending")
