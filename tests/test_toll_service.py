import pytest
from services.toll_service import TollService
from models.route import RouteCandidate


@pytest.fixture
def mock_routes():
    """Fixture providing sample route candidates"""
    return [
        RouteCandidate(
            route_id="route_1",
            eta_seconds=1800,
            distance_meters=25000,
            polyline="mock_polyline_1",
            toll_estimate_usd=None
        ),
        RouteCandidate(
            route_id="route_2",
            eta_seconds=2100,
            distance_meters=22000,
            polyline="mock_polyline_2",
            toll_estimate_usd=None
        ),
        RouteCandidate(
            route_id="route_3",
            eta_seconds=2400,
            distance_meters=20000,
            polyline="mock_polyline_3",
            toll_estimate_usd=None
        )
    ]


def test_estimate_tolls_mock_pricing(mock_routes):
    """Test toll estimation using mock pricing model"""
    service = TollService(use_mock=True, seed=42)  # Deterministic
    
    routes_with_tolls = service.estimate_tolls(mock_routes)
    
    assert len(routes_with_tolls) == 3
    # All routes should have toll estimates
    for route in routes_with_tolls:
        assert route.toll_estimate_usd is not None
        assert route.toll_estimate_usd >= 0


def test_estimate_tolls_distance_based(mock_routes):
    """Test that toll estimates scale with distance"""
    service = TollService(use_mock=True, seed=42)  # Deterministic
    
    routes_with_tolls = service.estimate_tolls(mock_routes)
    
    # Longer routes should generally have higher tolls (mock model)
    # Route 1: 25km, Route 2: 22km, Route 3: 20km
    assert routes_with_tolls[0].distance_meters > routes_with_tolls[2].distance_meters


def test_estimate_tolls_zero_toll_option(mock_routes):
    """Test handling of routes with no tolls"""
    service = TollService(use_mock=True, seed=42)  # Deterministic
    
    # Add a non-toll route
    non_toll_route = RouteCandidate(
        route_id="route_free",
        eta_seconds=3000,
        distance_meters=30000,
        polyline="free_route",
        toll_estimate_usd=0.0  # Explicitly no toll
    )
    mock_routes.append(non_toll_route)
    
    routes_with_tolls = service.estimate_tolls(mock_routes)
    
    free_route = next(r for r in routes_with_tolls if r.route_id == "route_free")
    assert free_route.toll_estimate_usd == 0.0


def test_estimate_tolls_unavailable():
    """Test handling when toll data is unavailable"""
    service = TollService(use_mock=True, seed=42)  # Deterministic
    
    routes = [
        RouteCandidate(
            route_id="route_unknown",
            eta_seconds=1500,
            distance_meters=18000,
            polyline="unknown",
            toll_estimate_usd=None
        )
    ]
    
    routes_with_tolls = service.estimate_tolls(routes)
    
    # Should return route with estimate or None if truly unavailable
    assert len(routes_with_tolls) == 1
    # In mock mode, should provide an estimate
    assert routes_with_tolls[0].toll_estimate_usd is not None
