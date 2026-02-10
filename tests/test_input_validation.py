import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_validate_coordinates_valid():
    """Test valid coordinates are accepted"""
    payload = {
        "origin": {"lat": 30.2672, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664},
        "preferences": {"toll_budget_usd": 10.0}
    }
    
    # Should not raise validation error (will fail on Mapbox token, but that's expected)
    response = client.post("/routes/optimize", json=payload)
    # Won't be 200 without valid Mapbox token, but should not be 422 (validation error)
    assert response.status_code != 422


def test_validate_latitude_too_high():
    """Test latitude > 90 is rejected"""
    payload = {
        "origin": {"lat": 91.0, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422
    assert "Latitude" in response.json()["detail"][0]["msg"]


def test_validate_latitude_too_low():
    """Test latitude < -90 is rejected"""
    payload = {
        "origin": {"lat": -91.0, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422


def test_validate_longitude_too_high():
    """Test longitude > 180 is rejected"""
    payload = {
        "origin": {"lat": 30.2672, "lng": 181.0},
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422
    assert "Longitude" in response.json()["detail"][0]["msg"]


def test_validate_longitude_too_low():
    """Test longitude < -180 is rejected"""
    payload = {
        "origin": {"lat": 30.2672, "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -181.0}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422


def test_validate_missing_lat():
    """Test missing latitude field is rejected"""
    payload = {
        "origin": {"lng": -97.7431},  # Missing lat
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422


def test_validate_missing_lng():
    """Test missing longitude field is rejected"""
    payload = {
        "origin": {"lat": 30.2672},  # Missing lng
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422


def test_validate_non_numeric_coordinates():
    """Test non-numeric coordinates are rejected"""
    payload = {
        "origin": {"lat": "thirty", "lng": -97.7431},
        "destination": {"lat": 30.2020, "lng": -97.6664}
    }
    
    response = client.post("/routes/optimize", json=payload)
    assert response.status_code == 422
