"""
Texas-wide toll pricing service
Accurate toll rates for major Texas metros: Austin, Houston, Dallas-Fort Worth, San Antonio
"""
from typing import List, Dict, Optional
from models.route import RouteCandidate
import re
from datetime import datetime, time


class TexasTollService:
    """
    Texas statewide toll road pricing service
    
    Covers major metro areas:
    - Austin: I-35 (free), 183, MoPac, SH-45, SH-130
    - Houston: Beltway 8, Hardy, Westpark, Fort Bend, Grand Parkway
    - Dallas-Fort Worth: Dallas North Tollway, PGBT, LBJ Express, 121
    - San Antonio: SH-130 South, Loop 1604 Toll
    """
    
    # Texas toll roads by region
    TOLL_ROADS = {
        # ========== AUSTIN AREA ==========
        '183_toll': {
            'patterns': [r'183.*toll', r'183.*express', r'us.*183.*toll', r'highway.*183.*toll'],
            'rate_per_mile': 0.65,
            'description': '183 Express/Toll (Austin)',
            'region': 'Austin',
            'dynamic_pricing': True,
            'peak_multiplier': 2.0,
            'congestion_sensitive': True
        },
        'sh45_toll': {
            'patterns': [r'sh.*45', r'state.*highway.*45', r'45.*toll', r'highway.*45'],
            'rate_per_mile': 0.47,
            'description': 'SH-45 Toll (Austin)',
            'region': 'Austin',
            'dynamic_pricing': False
        },
        'mopac_express': {
            'patterns': [r'mopac.*express', r'loop.*1.*express', r'mo[-\s]?pac.*toll', r'1.*loop.*express'],
            'rate_per_mile': 0.95,
            'description': 'MoPac Express (Austin)',
            'region': 'Austin',
            'dynamic_pricing': True,
            'peak_multiplier': 2.5,
            'congestion_sensitive': True
        },
        'sh130_toll': {
            'patterns': [r'sh.*130', r'state.*highway.*130', r'130.*toll', r'highway.*130'],
            'rate_per_mile': 0.17,
            'description': 'SH-130 Toll (Austin/San Antonio)',
            'region': 'Austin',
            'dynamic_pricing': False
        },
        'tx71_toll': {
            'patterns': [r'tx.*71.*toll', r'highway.*71.*toll', r'71.*express'],
            'rate_per_mile': 0.50,
            'description': 'TX-71 Toll (Austin)',
            'region': 'Austin',
            'dynamic_pricing': False
        },
        'manor_expressway': {
            'patterns': [r'manor.*expressway', r'manor.*toll', r'us.*290.*toll'],
            'rate_per_mile': 0.42,
            'description': 'Manor Expressway (Austin)',
            'region': 'Austin',
            'dynamic_pricing': False
        },
        
        # ========== HOUSTON AREA (HCTRA) ==========
        'sam_houston_tollway': {
            'patterns': [r'sam.*houston.*tollway', r'beltway.*8', r'belt.*way.*8', r'bw.*8', r'beltway 8'],
            'rate_per_mile': 0.50,
            'description': 'Sam Houston Tollway / Beltway 8 (Houston)',
            'region': 'Houston',
            'dynamic_pricing': True,
            'peak_multiplier': 1.8,
            'congestion_sensitive': True
        },
        'hardy_toll': {
            'patterns': [r'hardy.*toll', r'hardy.*road', r'sam.*houston.*parkway'],
            'rate_per_mile': 0.55,
            'description': 'Hardy Toll Road (Houston)',
            'region': 'Houston',
            'dynamic_pricing': False
        },
        'westpark_tollway': {
            'patterns': [r'westpark.*toll', r'west.*park.*toll'],
            'rate_per_mile': 0.60,
            'description': 'Westpark Tollway (Houston)',
            'region': 'Houston',
            'dynamic_pricing': False
        },
        'fort_bend_tollway': {
            'patterns': [r'fort.*bend.*toll', r'fb.*toll'],
            'rate_per_mile': 0.45,
            'description': 'Fort Bend Tollway (Houston)',
            'region': 'Houston',
            'dynamic_pricing': False
        },
        'grand_parkway': {
            'patterns': [r'grand.*parkway', r'sh.*99', r'99.*toll', r'state.*highway.*99'],
            'rate_per_mile': 0.40,
            'description': 'Grand Parkway SH-99 (Houston)',
            'region': 'Houston',
            'dynamic_pricing': False
        },
        'tomball_tollway': {
            'patterns': [r'tomball.*toll', r'249.*toll'],
            'rate_per_mile': 0.48,
            'description': 'Tomball Tollway (Houston)',
            'region': 'Houston',
            'dynamic_pricing': False
        },
        
        # ========== DALLAS-FORT WORTH AREA (NTTA) ==========
        'dallas_north_tollway': {
            'patterns': [r'dallas.*north.*tollway', r'dnt', r'north.*tollway.*dallas'],
            'rate_per_mile': 0.70,
            'description': 'Dallas North Tollway (DFW)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': True,
            'peak_multiplier': 1.9,
            'congestion_sensitive': True
        },
        'pgbt': {
            'patterns': [r'george.*bush.*turnpike', r'pgbt', r'bush.*tollway', r'president.*bush'],
            'rate_per_mile': 0.65,
            'description': 'President George Bush Turnpike (DFW)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': False
        },
        'sam_rayburn_tollway': {
            'patterns': [r'sam.*rayburn.*toll', r'srt', r'rayburn.*toll'],
            'rate_per_mile': 0.60,
            'description': 'Sam Rayburn Tollway (DFW)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': False
        },
        'lbj_express': {
            'patterns': [r'lbj.*express', r'lbj.*toll', r'635.*express', r'i[-\s]?635.*express'],
            'rate_per_mile': 0.85,
            'description': 'LBJ Express (DFW)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': True,
            'peak_multiplier': 2.2,
            'congestion_sensitive': True
        },
        'ntt_121': {
            'patterns': [r'121.*toll', r'tollway.*121', r'highway.*121.*toll'],
            'rate_per_mile': 0.55,
            'description': 'SH-121 Tollway (DFW)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': False
        },
        'chisholm_trail': {
            'patterns': [r'chisholm.*trail', r'chisholm.*parkway'],
            'rate_per_mile': 0.58,
            'description': 'Chisholm Trail Parkway (Fort Worth)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': False
        },
        'north_tarrant_express': {
            'patterns': [r'north.*tarrant.*express', r'nte', r'820.*express'],
            'rate_per_mile': 0.75,
            'description': 'North Tarrant Express (Fort Worth)',
            'region': 'Dallas-Fort Worth',
            'dynamic_pricing': True,
            'peak_multiplier': 2.0,
            'congestion_sensitive': True
        },
        
        # ========== SAN ANTONIO AREA ==========
        'loop_1604_toll': {
            'patterns': [r'1604.*toll', r'loop.*1604.*toll'],
            'rate_per_mile': 0.48,
            'description': 'Loop 1604 Toll (San Antonio)',
            'region': 'San Antonio',
            'dynamic_pricing': False
        },
        'sh_130_south': {
            'patterns': [r'sh.*130.*south', r'130.*toll.*south'],
            'rate_per_mile': 0.17,
            'description': 'SH-130 South Extension (San Antonio)',
            'region': 'San Antonio',
            'dynamic_pricing': False
        }
    }
    
    # Free highways across Texas
    FREE_HIGHWAYS = {
        # Interstates (all free)
        'i10': [r'i[-\s]?10\b', r'interstate.*10\b'],
        'i20': [r'i[-\s]?20\b', r'interstate.*20\b'],
        'i30': [r'i[-\s]?30\b', r'interstate.*30\b'],
        'i35': [r'i[-\s]?35\b', r'interstate.*35\b', r'ih.*35\b'],
        'i37': [r'i[-\s]?37\b', r'interstate.*37\b'],
        'i45': [r'i[-\s]?45\b', r'interstate.*45\b'],
        'i635': [r'i[-\s]?635\b', r'interstate.*635\b'],
        
        # US Highways (free unless specified as toll)
        'us183_free': [r'^us.*183$', r'^183$'],
        'us290_free': [r'^us.*290$', r'^290$'],
        'us59': [r'us.*59', r'^59$'],
        'us77': [r'us.*77', r'^77$'],
        
        # Texas State Highways (free unless specified)
        'tx71_free': [r'^tx.*71$', r'^71$'],
        'loop1_free': [r'^loop.*1$', r'^mopac$'],
    }
    
    # No-tag surcharge (pay-by-mail)
    NO_TAG_SURCHARGE = 1.50  # 50% surcharge without TxTag/TollTag/EZ TAG
    
    def __init__(self, use_dynamic_pricing: bool = True, has_toll_tag: bool = True):
        """
        Initialize Texas toll service
        
        Args:
            use_dynamic_pricing: Enable time-of-day and congestion-based dynamic pricing
            has_toll_tag: Whether vehicle has toll tag (TxTag/TollTag/EZ TAG)
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
        Estimate toll costs for routes using Texas-specific toll data
        
        Args:
            routes: List of route candidates
        
        Returns:
            Routes with accurate Texas toll estimates
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
        # Extract road segments from route geometry
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
        """Extract road segments from route geometry"""
        segments = []
        
        if hasattr(route, 'geometry') and isinstance(route.geometry, dict):
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
        Identify if a road name matches known Texas toll roads
        
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
        
        # Traffic congestion adjustment
        if toll_info.get('congestion_sensitive', False):
            expected_speed_mph = 65
            distance_miles = route.distance_meters / 1609.34
            
            if route.eta_seconds > 0:
                actual_speed_mph = (distance_miles / route.eta_seconds) * 3600
                
                if actual_speed_mph < expected_speed_mph * 0.7:
                    congestion_multiplier = 1.4
                    multiplier = min(multiplier * congestion_multiplier, peak_multiplier)
        
        return base_rate * multiplier
    
    def _fallback_toll_estimate(self, route: RouteCandidate) -> float:
        """
        Fallback toll estimation when road segments aren't available
        """
        distance_km = route.distance_meters / 1000
        distance_miles = distance_km * 0.621371
        
        if route.eta_seconds > 0:
            avg_speed_mph = (distance_miles / route.eta_seconds) * 3600
            
            # If average speed > 55 mph, likely using highways
            if avg_speed_mph > 55:
                estimated_toll_miles = distance_miles * 0.4
                base_estimate = estimated_toll_miles * 0.55
            else:
                base_estimate = distance_miles * 0.3 * 0.55
        else:
            base_estimate = distance_miles * 0.3 * 0.55
        
        # Apply no-tag surcharge if applicable
        if not self.has_toll_tag:
            base_estimate = base_estimate * self.NO_TAG_SURCHARGE
        
        return base_estimate
    
    def is_toll_free_route(self, route: RouteCandidate) -> bool:
        """Check if a route is toll-free"""
        return route.toll_estimate_usd == 0.0
