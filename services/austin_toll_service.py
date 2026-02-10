"""
Austin-specific toll pricing service
Accurate toll rates for Austin metro area highways with dynamic pricing
"""
from typing import List, Dict, Optional
from models.route import RouteCandidate
import re
from datetime import datetime, time


class AustinTollService:
    """
    Austin-area toll road pricing service
    
    Austin Major Highways:
    - I-35: No tolls (free)
    - US-183: Has toll/express lanes (183 Express/Toll)
    - SH-45: Toll road (SH-45 Toll)
    - MoPac/Loop 1: Has toll/express lanes (MoPac Express)
    - SH-130: Toll road (full highway toll)
    """
    
    # Austin toll road patterns (highway name variations in Mapbox data)
    TOLL_ROADS = {
        '183_toll': {
            'patterns': [r'183.*toll', r'183.*express', r'us.*183.*toll', r'highway.*183.*toll'],
            'rate_per_mile': 0.65,  # Base rate for 183 Express
            'description': '183 Express/Toll',
            'dynamic_pricing': True,  # Uses congestion-based pricing
            'peak_multiplier': 2.0,   # Up to 2x during peak times
            'congestion_sensitive': True
        },
        'sh45_toll': {
            'patterns': [r'sh.*45', r'state.*highway.*45', r'45.*toll', r'highway.*45'],
            'rate_per_mile': 0.47,  # Fixed rate for SH-45
            'description': 'SH-45 Toll',
            'dynamic_pricing': False
        },
        'mopac_express': {
            'patterns': [r'mopac.*express', r'loop.*1.*express', r'mo[-\s]?pac.*toll', r'1.*loop.*express'],
            'rate_per_mile': 0.95,  # Base rate for MoPac Express
            'description': 'MoPac Express',
            'dynamic_pricing': True,  # Uses real-time congestion pricing
            'peak_multiplier': 2.5,   # Can be 2.5x during heavy congestion
            'congestion_sensitive': True
        },
        'sh130_toll': {
            'patterns': [r'sh.*130', r'state.*highway.*130', r'130.*toll', r'highway.*130'],
            'rate_per_mile': 0.17,  # Lower fixed rate for SH-130
            'description': 'SH-130 Toll',
            'dynamic_pricing': False
        },
        'tx71_toll': {
            'patterns': [r'tx.*71.*toll', r'highway.*71.*toll', r'71.*express'],
            'rate_per_mile': 0.50,
            'description': 'TX-71 Toll',
            'dynamic_pricing': False
        },
        'manor_expressway': {
            'patterns': [r'manor.*expressway', r'manor.*toll', r'us.*290.*toll'],
            'rate_per_mile': 0.42,
            'description': 'Manor Expressway',
            'dynamic_pricing': False
        }
    }
    
    # Free highways in Austin
    FREE_HIGHWAYS = {
        'i35': [r'i[-\s]?35', r'interstate.*35', r'ih.*35'],
        'i35_frontage': [r'i[-\s]?35.*frontage', r'i[-\s]?35.*access'],
        'us183_free': [r'^us.*183$', r'^183$'],  # Regular 183 (not express)
        'loop1_free': [r'^loop.*1$', r'^mopac$'],  # Regular MoPac lanes (not express)
        'us290_free': [r'^us.*290$', r'^290$'],
        'tx71_free': [r'^tx.*71$', r'^71$']
    }
    
    # No-tag surcharge rates
    NO_TAG_SURCHARGE = 1.50  # 50% surcharge for vehicles without TxTag/EZ Tag
    
    def __init__(self, use_dynamic_pricing: bool = True, has_toll_tag: bool = True):
        """
        Initialize Austin toll service
        
        Args:
            use_dynamic_pricing: Enable time-of-day and congestion-based dynamic pricing
            has_toll_tag: Whether vehicle has TxTag/EZ Tag (False = pay-by-mail rates)
        """
        self.use_dynamic_pricing = use_dynamic_pricing
        self.has_toll_tag = has_toll_tag
        self.compiled_toll_patterns = self._compile_patterns(self.TOLL_ROADS)
        self.compiled_free_patterns = self._compile_patterns(self.FREE_HIGHWAYS)
    
    def _compile_patterns(self, road_dict: Dict) -> Dict:
        """Precompile regex patterns for performance"""
        compiled = {}
        for road_id, road_data in road_dict.items():
            patterns = road_data if isinstance(road_data, list) else road_data.get('patterns', [])
            compiled[road_id] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        return compiled
    
    def estimate_tolls(self, routes: List[RouteCandidate]) -> List[RouteCandidate]:
        """
        Estimate toll costs for routes using Austin-specific toll data
        
        Args:
            routes: List of route candidates
        
        Returns:
            Routes with accurate Austin toll estimates
        """
        for route in routes:
            if route.toll_estimate_usd is not None:
                continue
            
            toll_cost = self._calculate_route_toll(route)
            route.toll_estimate_usd = round(toll_cost, 2)
        
        return routes
    
    def _calculate_route_toll(self, route: RouteCandidate) -> float:
        """
        Calculate toll cost for a single route by analyzing road names
        
        Args:
            route: Route candidate with geometry and distance
        
        Returns:
            Total toll cost in USD
        """
        # Extract road segments from route geometry properties if available
        road_segments = self._extract_road_segments(route)
        
        if not road_segments:
            # Fallback: estimate based on distance
            return self._fallback_toll_estimate(route)
        
        total_toll = 0.0
        
        for segment in road_segments:
            road_name = segment.get('name', '').lower()
            distance_miles = segment.get('distance_meters', 0) / 1609.34
            
            # Check if this is a known toll road
            toll_info = self._identify_toll_road(road_name)
            
            if toll_info:
                base_rate = toll_info['rate_per_mile']
                
                # Apply dynamic pricing if enabled
                if self.use_dynamic_pricing and toll_info.get('dynamic_pricing', False):
                    rate = self._apply_dynamic_pricing(base_rate, toll_info, route)
                else:
                    rate = base_rate
                
                # Apply no-tag surcharge if vehicle doesn't have toll tag
                if not self.has_toll_tag:
                    rate = rate * self.NO_TAG_SURCHARGE
                
                segment_toll = distance_miles * rate
                total_toll += segment_toll
        
        return total_toll
    
    def _extract_road_segments(self, route: RouteCandidate) -> List[Dict]:
        """
        Extract road segments from route geometry
        
        Returns:
            List of segments with road names and distances
        """
        segments = []
        
        # Check if route has geometry with legs/steps
        if hasattr(route, 'geometry') and isinstance(route.geometry, dict):
            # Try to access steps from geometry if available
            # Note: This requires the route to have step-level detail
            if 'legs' in route.geometry:
                for leg in route.geometry['legs']:
                    if 'steps' in leg:
                        for step in leg['steps']:
                            segments.append({
                                'name': step.get('name', ''),
                                'distance_meters': step.get('distance', 0)
                            })
        
        return segments
    
    def _identify_toll_road(self, road_name: str) -> Optional[Dict]:
        """
        Identify if a road name matches known Austin toll roads
        
        Args:
            road_name: Name of the road (lowercase)
        
        Returns:
            Toll road info dict or None
        """
        if not road_name:
            return None
        
        # Check toll roads
        for toll_id, patterns in self.compiled_toll_patterns.items():
            for pattern in patterns:
                if pattern.search(road_name):
                    return self.TOLL_ROADS[toll_id]
        
        return None
    
    def _apply_dynamic_pricing(self, base_rate: float, toll_info: Dict, route: RouteCandidate) -> float:
        """
        Apply dynamic pricing based on time of day and traffic congestion
        
        Args:
            base_rate: Base rate per mile
            toll_info: Toll road configuration
            route: Route candidate with traffic data
        
        Returns:
            Adjusted rate per mile
        """
        multiplier = 1.0
        
        # Time-of-day pricing
        current_time = datetime.now().time()
        peak_multiplier = toll_info.get('peak_multiplier', 1.5)
        
        # Morning rush: 7:00 AM - 9:30 AM
        if time(7, 0) <= current_time <= time(9, 30):
            multiplier = peak_multiplier
        # Evening rush: 4:30 PM - 7:00 PM
        elif time(16, 30) <= current_time <= time(19, 0):
            multiplier = peak_multiplier
        # Mid-day moderate: 11:00 AM - 2:00 PM
        elif time(11, 0) <= current_time <= time(14, 0):
            multiplier = 1.3
        # Off-peak discount: 9:00 PM - 6:00 AM
        elif current_time >= time(21, 0) or current_time <= time(6, 0):
            multiplier = 0.6
        # Otherwise regular rate (1.0)
        
        # Traffic congestion adjustment (if route is slower than expected)
        if toll_info.get('congestion_sensitive', False):
            expected_speed_mph = 65  # Expected highway speed
            distance_miles = route.distance_meters / 1609.34
            
            if route.eta_seconds > 0:
                actual_speed_mph = (distance_miles / route.eta_seconds) * 3600
                
                # If significantly slower than expected, increase toll (congestion pricing)
                if actual_speed_mph < expected_speed_mph * 0.7:  # More than 30% slower
                    congestion_multiplier = 1.4
                    multiplier = min(multiplier * congestion_multiplier, peak_multiplier)
        
        return base_rate * multiplier
    
    def _fallback_toll_estimate(self, route: RouteCandidate) -> float:
        """
        Fallback toll estimation when road segments aren't available
        Uses distance-based heuristics
        
        Args:
            route: Route candidate
        
        Returns:
            Estimated toll cost
        """
        distance_km = route.distance_meters / 1000
        distance_miles = distance_km * 0.621371
        
        # Heuristic: If route duration suggests highway use, estimate toll
        # Average speed calculation
        if route.eta_seconds > 0:
            avg_speed_mph = (distance_miles / route.eta_seconds) * 3600
            
            # If average speed > 55 mph, likely using highways
            if avg_speed_mph > 55:
                # Assume 40% of highway miles might be toll roads
                estimated_toll_miles = distance_miles * 0.4
                # Use average Austin toll rate
                base_estimate = estimated_toll_miles * 0.55
            else:
                # Conservative estimate: 30% chance of using toll roads
                base_estimate = distance_miles * 0.3 * 0.55
        else:
            base_estimate = distance_miles * 0.3 * 0.55
        
        # Apply no-tag surcharge if applicable
        if not self.has_toll_tag:
            base_estimate = base_estimate * self.NO_TAG_SURCHARGE
        
        return base_estimate
    
    def is_toll_free_route(self, route: RouteCandidate) -> bool:
        """
        Check if a route is toll-free (uses only I-35 and free highways)
        
        Args:
            route: Route candidate
        
        Returns:
            True if route appears toll-free
        """
        return route.toll_estimate_usd == 0.0
