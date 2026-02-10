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
        Optimize route selection with priority display order:
        1. No-toll route (cheapest/minimal toll)
        2. Fastest route (with all tolls, regardless of budget)
        3. Other routes within budget, sorted by fastest
        
        Args:
            routes: List of route candidates with toll estimates
            budget: Maximum toll budget in USD
        
        Returns:
            Dict with recommended_route_id, routes_ranked, advisories
        """
        if not routes:
            return {
                "budget_usd": budget,
                "recommended_route_id": None,
                "routes_ranked": [],
                "advisories": ["No routes available"]
            }
        
        # Annotate all routes
        routes_annotated = []
        for route in routes:
            toll = route.toll_estimate_usd if route.toll_estimate_usd is not None else 0.0
            
            annotated = {
                "route_id": route.route_id,
                "eta_seconds": route.eta_seconds,
                "distance_meters": route.distance_meters,
                "toll_estimate_usd": toll,
                "budget_status": "WITHIN" if toll <= budget else "EXCEEDS",
                "exceeds_by_usd": max(0, round(toll - budget, 2)),
                "polyline": route.polyline,
                "geometry": route.geometry,
                "route_obj": route
            }
            routes_annotated.append(annotated)
        
        # Sort and categorize
        no_toll_route = min(routes_annotated, key=lambda r: r["toll_estimate_usd"])
        fastest_overall = min(routes_annotated, key=lambda r: r["eta_seconds"])
        within_budget = [r for r in routes_annotated if r["budget_status"] == "WITHIN"]
        within_budget_sorted = sorted(within_budget, key=lambda r: r["eta_seconds"])
        
        # Check if we actually have a toll-free route (very low/zero toll)
        has_true_no_toll = no_toll_route["toll_estimate_usd"] < 0.50  # Less than 50 cents = toll-free
        
        # Determine recommended route (fastest within budget)
        if within_budget_sorted:
            recommended_id = within_budget_sorted[0]["route_id"]
        else:
            recommended_id = no_toll_route["route_id"]
        
        # Build display order: no-toll/cheapest, fastest, then others in budget
        display_order = []
        added_ids = set()
        
        # 1. Add no-toll/cheapest route first
        if has_true_no_toll:
            no_toll_route["reason"] = f"Toll-free route - I-35 only ({(no_toll_route['eta_seconds']/60):.0f} min)"
        else:
            no_toll_route["reason"] = f"Lowest toll option - ${no_toll_route['toll_estimate_usd']:.2f} ({(no_toll_route['eta_seconds']/60):.0f} min)"
        no_toll_route["display_priority"] = 1
        display_order.append(no_toll_route)
        added_ids.add(no_toll_route["route_id"])
        
        # 2. Add fastest route (if different from no-toll)
        if fastest_overall["route_id"] not in added_ids:
            fastest_overall["reason"] = f"Fastest route - {(fastest_overall['eta_seconds']/60):.0f} min (${fastest_overall['toll_estimate_usd']:.2f} toll)"
            fastest_overall["display_priority"] = 2
            display_order.append(fastest_overall)
            added_ids.add(fastest_overall["route_id"])
        
        # 3. Add other routes within budget (sorted by fastest)
        priority = 3
        for route in within_budget_sorted:
            if route["route_id"] not in added_ids:
                is_recommended = route["route_id"] == recommended_id
                if is_recommended:
                    route["reason"] = f"⭐ Recommended - Best balance of time and cost"
                else:
                    time_diff = (route["eta_seconds"] - within_budget_sorted[0]["eta_seconds"]) / 60
                    route["reason"] = f"Within budget (+{time_diff:.0f} min vs fastest)"
                route["display_priority"] = priority
                display_order.append(route)
                added_ids.add(route["route_id"])
                priority += 1
        
        # 4. Add any remaining routes that exceed budget
        exceeding = [r for r in routes_annotated if r["route_id"] not in added_ids]
        for route in sorted(exceeding, key=lambda r: r["eta_seconds"]):
            route["reason"] = f"Exceeds budget by ${route['exceeds_by_usd']:.2f}"
            route["display_priority"] = priority
            display_order.append(route)
            priority += 1
        
        # Clean up route_obj from response
        for route in display_order:
            route.pop("route_obj", None)
        
        # Generate advisories
        advisories = []
        if not within_budget:
            advisories.append(
                f"No routes within ${budget:.2f} budget. Consider no-toll option or increase budget."
            )
        
        return {
            "budget_usd": budget,
            "recommended_route_id": recommended_id,
            "routes_ranked": display_order,
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
