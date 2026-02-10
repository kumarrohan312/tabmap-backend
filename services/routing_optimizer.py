from typing import List, Dict, Optional
from models.route import RouteCandidate


class RoutingOptimizer:
    """Core optimization engine for budget-aware routing"""
    
    def optimize_routes(
        self,
        routes: List[RouteCandidate],
        budget: float
    ) -> Dict:
        """
        Optimize route selection with two primary options:
        1. NO TOLL - Toll-free/cheapest route (avoid all tolls)
        2. BUDGET - Fastest route within budget (spend UP TO budget for speed)
        
        Args:
            routes: List of route candidates with toll estimates
            budget: Maximum toll budget in USD
        
        Returns:
            Dict with no_toll_option, budget_option, alternatives, advisories
        """
        if not routes:
            return {
                "budget_usd": budget,
                "no_toll_option": None,
                "budget_option": None,
                "alternatives": [],
                "advisories": ["No routes available"]
            }
        
        # Annotate all routes
        routes_annotated = []
        for route in routes:
            toll = route.toll_estimate_usd if route.toll_estimate_usd is not None else 0.0
            
            annotated = {
                "route_id": route.route_id,
                "eta_seconds": route.eta_seconds,
                "eta_minutes": round(route.eta_seconds / 60, 0),
                "distance_meters": route.distance_meters,
                "distance_miles": round(route.distance_meters / 1609.34, 1),
                "toll_estimate_usd": toll,
                "within_budget": toll <= budget,
                "polyline": route.polyline,
                "geometry": route.geometry,
            }
            routes_annotated.append(annotated)
        
        # 1. NO TOLL OPTION - Cheapest route (ideally $0)
        no_toll_route = min(routes_annotated, key=lambda r: r["toll_estimate_usd"])
        no_toll_route["option_type"] = "NO_TOLL"
        no_toll_route["label"] = "No Toll Route" if no_toll_route["toll_estimate_usd"] < 0.50 else "Cheapest Route"
        no_toll_route["description"] = f"${no_toll_route['toll_estimate_usd']:.2f} toll • {no_toll_route['eta_minutes']:.0f} min • {no_toll_route['distance_miles']:.1f} mi"
        
        # 2. BUDGET OPTION - Fastest route within budget (maximize speed for budget)
        within_budget = [r for r in routes_annotated if r["within_budget"]]
        
        if within_budget:
            budget_route = min(within_budget, key=lambda r: r["eta_seconds"])
            budget_route["option_type"] = "BUDGET"
            budget_route["label"] = f"Best Value (${budget:.0f} Budget)"
            time_saved = no_toll_route["eta_minutes"] - budget_route["eta_minutes"]
            budget_route["description"] = f"${budget_route['toll_estimate_usd']:.2f} toll • {budget_route['eta_minutes']:.0f} min • Saves {time_saved:.0f} min"
        else:
            # No routes within budget - use cheapest as fallback
            budget_route = no_toll_route.copy()
            budget_route["option_type"] = "BUDGET"
            budget_route["label"] = f"Best Value (${budget:.0f} Budget)"
            budget_route["description"] = f"No routes within budget - showing cheapest option"
        
        # 3. ALTERNATIVES - Other routes (fastest overall, other within budget)
        alternatives = []
        added_ids = {no_toll_route["route_id"], budget_route["route_id"]}
        
        # Add fastest overall if different and exceeds budget
        fastest_overall = min(routes_annotated, key=lambda r: r["eta_seconds"])
        if fastest_overall["route_id"] not in added_ids:
            fastest_overall["option_type"] = "ALTERNATIVE"
            fastest_overall["label"] = "Fastest Route (Exceeds Budget)"
            fastest_overall["description"] = f"${fastest_overall['toll_estimate_usd']:.2f} toll • {fastest_overall['eta_minutes']:.0f} min • ${fastest_overall['toll_estimate_usd'] - budget:.2f} over"
            alternatives.append(fastest_overall)
            added_ids.add(fastest_overall["route_id"])
        
        # Add other routes within budget
        for route in sorted(within_budget, key=lambda r: r["eta_seconds"]):
            if route["route_id"] not in added_ids:
                route["option_type"] = "ALTERNATIVE"
                route["label"] = "Alternative Route"
                route["description"] = f"${route['toll_estimate_usd']:.2f} toll • {route['eta_minutes']:.0f} min"
                alternatives.append(route)
                added_ids.add(route["route_id"])
        
        # Generate advisories
        advisories = []
        if not within_budget:
            advisories.append(f"⚠️ No routes within ${budget:.2f} budget. Choose No Toll option or increase budget.")
        elif budget_route["toll_estimate_usd"] < budget * 0.5:
            advisories.append(f"💡 Budget route only uses ${budget_route['toll_estimate_usd']:.2f} of ${budget:.2f} budget and is fastest option.")
        
        return {
            "budget_usd": budget,
            "no_toll_option": no_toll_route,
            "budget_option": budget_route,
            "alternatives": alternatives,
            "advisories": advisories
        }
    
    def _generate_explanation(
        self,
        annotated: Dict,
        route: RouteCandidate,
        recommended_id: str,
        budget: float,
        within_budget_routes: List[RouteCandidate],
        all_routes: List[RouteCandidate]
    ) -> str:
        """Generate explanation text for route recommendation"""
        
        if annotated["route_id"] != recommended_id:
            # Not recommended
            if annotated["budget_status"] == "EXCEEDS":
                return f"Exceeds budget by ${annotated['exceeds_by_usd']:.2f}"
            else:
                # Within budget but not fastest
                recommended_route = next(r for r in all_routes if r.route_id == recommended_id)
                time_diff_sec = annotated["eta_seconds"] - recommended_route.eta_seconds
                time_diff_min = time_diff_sec // 60
                return f"Slower by {time_diff_min} min compared to recommended route"
        
        # This is the recommended route
        if not within_budget_routes:
            return "Cheapest option (no routes within budget)"
        
        # Find cheapest route within budget
        cheapest_in_budget = min(within_budget_routes, key=lambda r: r.toll_estimate_usd or 0.0)
        
        if route.route_id == cheapest_in_budget.route_id:
            return f"Cheapest within your ${budget:.2f} budget"
        
        # Calculate time savings vs cheapest
        time_saved_sec = cheapest_in_budget.eta_seconds - route.eta_seconds
        time_saved_min = time_saved_sec // 60
        
        if time_saved_min > 0:
            return f"Fastest within your ${budget:.2f} budget; saves {time_saved_min} min vs cheapest"
        else:
            return f"Fastest within your ${budget:.2f} budget"
