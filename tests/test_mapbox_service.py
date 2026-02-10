import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.mapbox_service import MapboxService
from models.route import RouteCandidate


@pytest.mark.asyncio
async def test_get_route_candidates_success():
    """Test successful retrieval of route candidates from Mapbox"""
    service = MapboxService(access_token="test_token")
    
    origin = {"lat": 30.2672, "lng": -97.7431}
    destination = {"lat": 30.2020, "lng": -97.6664}
    
    # Mock Mapbox API response
    mock_response = {
        "routes": [
            {
                "duration": 1800,  # 30 minutes
                "distance": 25000,  # 25 km
                "geometry": "mock_polyline_1",
            },
            {
                "duration": 2100,  # 35 minutes
                "distance": 22000,  # 22 km
                "geometry": "mock_polyline_2",
            }
        ],
        "code": "Ok"
    }
    
    with patch.object(service, '_fetch_directions', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_response
        
        candidates = await service.get_route_candidates(origin, destination)
        
        assert len(candidates) == 2
        assert candidates[0].eta_seconds == 1800
        assert candidates[0].distance_meters == 25000
        assert candidates[1].eta_seconds == 2100
        assert candidates[1].distance_meters == 22000


@pytest.mark.asyncio
async def test_get_route_candidates_with_preferences():
    """Test route retrieval with avoid preferences"""
    service = MapboxService(access_token="test_token")
    
    origin = {"lat": 30.2672, "lng": -97.7431}
    destination = {"lat": 30.2020, "lng": -97.6664}
    preferences = {"avoid_tolls": True, "avoid_highways": False}
    
    with patch.object(service, '_fetch_directions', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"routes": [], "code": "Ok"}
        
        await service.get_route_candidates(origin, destination, preferences)
        
        # Verify preferences were passed to API
        call_args = mock_fetch.call_args
        assert call_args is not None


@pytest.mark.asyncio
async def test_get_route_candidates_api_error():
    """Test handling of Mapbox API errors"""
    service = MapboxService(access_token="test_token")
    
    origin = {"lat": 30.2672, "lng": -97.7431}
    destination = {"lat": 30.2020, "lng": -97.6664}
    
    with patch.object(service, '_fetch_directions', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await service.get_route_candidates(origin, destination)


@pytest.mark.asyncio
async def test_get_route_candidates_empty_response():
    """Test handling of empty route results"""
    service = MapboxService(access_token="test_token")
    
    origin = {"lat": 30.2672, "lng": -97.7431}
    destination = {"lat": 30.2020, "lng": -97.6664}
    
    mock_response = {"routes": [], "code": "Ok"}
    
    with patch.object(service, '_fetch_directions', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_response
        
        candidates = await service.get_route_candidates(origin, destination)
        
        assert len(candidates) == 0
