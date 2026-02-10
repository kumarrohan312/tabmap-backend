from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.optimize import router as optimize_router
import os
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Toll Budget Routing API",
    description="Backend API for budget-aware route optimization",
    version="1.0.0"
)

# CORS configuration - supports both JSON array and comma-separated string
cors_origins_str = os.getenv("CORS_ORIGINS", '["http://localhost:19000","http://localhost:19006"]')
try:
    # Try parsing as JSON array first
    allowed_origins = json.loads(cors_origins_str)
except json.JSONDecodeError:
    # Fall back to comma-separated string
    allowed_origins = cors_origins_str.split(",")

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(optimize_router, prefix="/routes", tags=["routing"])

@app.get("/")
async def root():
    return {"message": "Toll Budget Routing API", "status": "active"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
