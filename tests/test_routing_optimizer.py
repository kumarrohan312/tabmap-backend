import pytest
from services.routing_optimizer import RoutingOptimizer
from models.route import RouteCandidate


@pytest.fixture
def sample_routes():
    """Sample routes with varying tolls and ETAs"""
    return [
        RouteCandidate(
            route_id="route_1",
            eta_seconds=1800,  # 30 min - fastest
            distance_meters=25000,
            toll_estimate_usd=9.8,
            polyline="poly1"
        ),
        RouteCandidate(
            route_id="route_2",
            eta_seconds=2100,  # 35 min
            distance_meters=22000,
            toll_estimate_usd=5.0,
            polyline="poly2"
        ),
        RouteCandidate(
            route_id="route_3",
            eta_seconds=2400,  # 40 min
            distance_meters=20000,
            toll_estimate_usd=0.0,  # Free
            polyline="poly3"
        ),
        RouteCandidate(
            route_id="route_4",
            eta_seconds=2700,  # 45 min - slowest
            distance_meters=30000,
            toll_estimate_usd=12.0,  # Expensive
            polyline="poly4"
        )
    ]


def test_optimize_routes_within_budget(sample_routes):
    """Test optimization recommends fastest route within budget"""
    optimizer = RoutingOptimizer()
    budget = 10.0
    
    result = optimizer.optimize_routes(sample_routes, budget)
    
    # Should recommend route_1 (fastest at $9.80, under $10 budget)
    assert result["recommended_route_id"] == "route_1"
    assert result["budget_usd"] == 10.0
    
    # Verify route details
    recommended = result["routes_ranked"][0]
    assert recommended["route_id"] == "route_1"
    assert recommended["budget_status"] == "WITHIN"
    assert recommended["exceeds_by_usd"] == 0.0


def test_optimize_routes_filters_exceeding_budget(sample_routes):
    """Test routes exceeding budget are marked correctly"""
    optimizer = RoutingOptimizer()
    budget = 5.0
    
    result = optimizer.optimize_routes(sample_routes, budget)
    
    # Should recommend route_2 (fastest within $5 budget)
    assert result["recommended_route_id"] == "route_2"
    
    # Check budget status on all routes
    routes = {r["route_id"]: r for r in result["routes_ranked"]}
    
    assert routes["route_2"]["budget_status"] == "WITHIN"
    assert routes["route_3"]["budget_status"] == "WITHIN"
    assert routes["route_1"]["budget_status"] == "EXCEEDS"
    assert routes["route_1"]["exceeds_by_usd"] == 4.8
    assert routes["route_4"]["budget_status"] == "EXCEEDS"


def test_optimize_no_routes_within_budget(sample_routes):
    """Test handling when no routes fit budget"""
    optimizer = RoutingOptimizer()
    budget = 0.0  # No budget
    
    result = optimizer.optimize_routes(sample_routes, budget)
    
    # Should recommend free route (route_3)
    assert result["recommended_route_id"] == "route_3"
    
    # Check advisory message
    advisories = result.get("advisories", [])
    # With $0 budget, only free route fits
    within_budget_routes = [r for r in result["routes_ranked"] if r["budget_status"] == "WITHIN"]
    assert len(within_budget_routes) >= 1


def test_optimize_ranking_by_eta(sample_routes):
    """Test routes are ranked by ETA within budget"""
    optimizer = RoutingOptimizer()
    budget = 20.0  # All routes within budget
    
    result = optimizer.optimize_routes(sample_routes, budget)
    
    # All routes should be WITHIN budget
    within_routes = [r for r in result["routes_ranked"] if r["budget_status"] == "WITHIN"]
    
    # Should be sorted by ETA (fastest first)
    etas = [r["eta_seconds"] for r in within_routes]
    assert etas == sorted(etas)
    
    # Fastest should be recommended
    assert result["recommended_route_id"] == "route_1"


def test_optimize_with_zero_budget():
    """Test optimization with zero budget finds free route"""
    routes = [
        RouteCandidate(
            route_id="toll_route",
            eta_seconds=1500,
            distance_meters=20000,
            toll_estimate_usd=8.0,
            polyline="poly1"
        ),
        RouteCandidate(
            route_id="free_route",
            eta_seconds=2000,
            distance_meters=25000,
            toll_estimate_usd=0.0,
            polyline="poly2"
        )
    ]
    
    optimizer = RoutingOptimizer()
    result = optimizer.optimize_routes(routes, budget=0.0)
    
    # Should recommend free route
    assert result["recommended_route_id"] == "free_route"
    
    recommended = result["routes_ranked"][0]
    assert recommended["budget_status"] == "WITHIN"
    assert recommended["toll_estimate_usd"] == 0.0


def test_optimize_generates_recommendation_explanation(sample_routes):
    """Test recommendation includes explanation"""
    optimizer = RoutingOptimizer()
    budget = 10.0
    
    result = optimizer.optimize_routes(sample_routes, budget)
    
    recommended = result["routes_ranked"][0]
    
    # Should have explanation text
    assert "reason" in recommended
    assert len(recommended["reason"]) > 0
    assert "budget" in recommended["reason"].lower() or "saves" in recommended["reason"].lower()
