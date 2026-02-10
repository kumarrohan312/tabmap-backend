# Toll Budget Routing - Backend API

FastAPI backend for budget-aware route optimization.

## Features

- **Mapbox Integration**: Retrieve multiple route candidates
- **Toll Estimation**: Mock toll pricing for MVP (extensible to real providers)
- **Budget Optimization**: Filter routes by toll budget, recommend fastest within budget
- **Smart Recommendations**: Generate explanations for route suggestions
- **Comprehensive Testing**: 19 unit and integration tests

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Mapbox access token:
```
MAPBOX_ACCESS_TOKEN=your_actual_token_here
```

### 3. Run Tests

```bash
python -m pytest tests/ -v
```

### 4. Start Server

```bash
python main.py
```

API will be available at `http://localhost:8000`

## API Endpoints

### POST `/routes/optimize`

Optimize route selection based on toll budget.

**Request Body:**
```json
{
  "origin": {"lat": 30.2672, "lng": -97.7431},
  "destination": {"lat": 30.2020, "lng": -97.6664},
  "preferences": {
    "toll_budget_usd": 10.0,
    "avoid_tolls": false,
    "avoid_highways": false
  }
}
```

**Response:**
```json
{
  "budget_usd": 10.0,
  "recommended_route_id": "route_1",
  "routes_ranked": [
    {
      "route_id": "route_1",
      "eta_seconds": 1800,
      "distance_meters": 25000,
      "toll_estimate_usd": 9.8,
      "budget_status": "WITHIN",
      "exceeds_by_usd": 0.0,
      "reason": "Fastest within your $10.00 budget; saves 18 min vs cheapest"
    }
  ],
  "advisories": []
}
```

### GET `/health`

Health check endpoint.

## Architecture

```
backend/
├── main.py                   # FastAPI application entry
├── routes/
│   └── optimize.py          # /routes/optimize endpoint
├── services/
│   ├── mapbox_service.py    # Mapbox Directions API client
│   ├── toll_service.py      # Toll estimation (mock + real)
│   └── routing_optimizer.py # Core budget optimization logic
├── models/
│   └── route.py             # Pydantic data models
└── tests/
    ├── test_api_routes.py
    ├── test_mapbox_service.py
    ├── test_routing_optimizer.py
    └── test_toll_service.py
```

## Testing

Run specific test files:
```bash
python -m pytest tests/test_routing_optimizer.py -v
```

Run with coverage:
```bash
python -m pytest tests/ --cov=services --cov=routes
```

## Optimization Algorithm

1. **Retrieve Candidates**: Get 2-3 route options from Mapbox
2. **Estimate Tolls**: Apply mock pricing model (or real provider)
3. **Filter by Budget**: `toll_total ≤ user_budget`
4. **Rank by ETA**: Select fastest route among valid options
5. **Generate Explanations**: Create user-friendly recommendation text

## Next Steps

- [ ] Integrate real toll data provider (TollGuru, HERE, etc.)
- [ ] Add Redis caching for route results
- [ ] Implement rate limiting
- [ ] Add request logging and analytics
- [ ] Deploy to production (AWS/GCP/Azure)
