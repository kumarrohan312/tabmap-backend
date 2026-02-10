import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
from models.route import RouteCandidate


client = TestClient(app)


@pytest.fixture
def mock_mapbox_response():
    """Mock Mapbox route candidates"""
    return [
        RouteCandidate(
            route_id="route_1",
            eta_seconds=1800,
            distance_meters=25000,
            polyline="poly1",
            toll_estimate_usd=None
        ),
        RouteCandidate(
            route_id="route_2",
            eta_seconds=2100,
            distance_meters=22000,
            polyline="poly2",
            toll_estimate_usd=None
        )
    ]


@patch.dict("os.environ", {"MAPBOX_ACCESS_TOKEN": "test_token"})
@patch("routes.optimize.MapboxService.get_route_candidates", new_callable=AsyncMock)
def test_optimize_routes_endpoint_success(mock_get_routes, mock_mapbox_response):
    """Test /routes/optimize endpoint returns optimized routes"""
    mock_get_routes.return_value = mock_mapbox_response
    
    payload = {
        "origin": {"lat": 30.2672, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664},
        "preferences": {
            "toll_budget_usd": 10.0,
            "avoid_tolls": False,
            "avoid_highways": False
        }
    }
    
    response = client.post("/routes/optimize", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "recommended_route_id" in data
    assert "routes_ranked" in data
    assert "budget_usd" in data
    assert data["budget_usd"] == 10.0
    assert len(data["routes_ranked"]) == 2


@patch.dict("os.environ", {"MAPBOX_ACCESS_TOKEN": "test_token"})
@patch("routes.optimize.MapboxService.get_route_candidates", new_callable=AsyncMock)
def test_optimize_routes_with_budget_constraint(mock_get_routes, mock_mapbox_response):
    """Test budget constraint is properly applied"""
    mock_get_routes.return_value = mock_mapbox_response
    
    payload = {
        "origin": {"lat": 30.2672, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664},
        "preferences": {
            "toll_budget_usd": 5.0  # Strict budget
        }
    }
    
    response = client.post("/routes/optimize", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify routes are annotated with budget status
    for route in data["routes_ranked"]:
        assert "budget_status" in route
        assert route["budget_status"] in ["WITHIN", "EXCEEDS"]


@patch.dict("os.environ", {"MAPBOX_ACCESS_TOKEN": "test_token"})
@patch("routes.optimize.MapboxService.get_route_candidates", new_callable=AsyncMock)
def test_optimize_routes_no_candidates(mock_get_routes):
    """Test handling when no routes are found"""
    mock_get_routes.return_value = []  # No routes
    
    payload = {
        "origin": {"lat": 30.2672, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    
    assert response.status_code == 404
    assert "No routes found" in response.json()["detail"]


def test_optimize_routes_missing_mapbox_token():
    """Test error when Mapbox token not configured"""
    with patch.dict("os.environ", {}, clear=True):
        payload = {
            "origin": {"lat": 30.2672, "lng": -97.7431},
            "destination": {"lat": 30.2020, "lng": -97.6664}
        }
        
        response = client.post("/routes/optimize", json=payload)
        
        assert response.status_code == 500
        assert "token not configured" in response.json()["detail"]


def test_health_endpoint():
    """Test routing service health check"""
    response = client.get("/routes/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
