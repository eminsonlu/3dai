"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.routers import routes, roads, neighborhoods, optimize

app = FastAPI(title="Trash Collection Routes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(routes.router)
app.include_router(roads.router)
app.include_router(neighborhoods.router)
app.include_router(optimize.router)


@app.get("/")
async def root():
    """Health check endpoint.

    Returns:
        Status and message indicating API is running
    """
    return {"status": "ok", "message": "Trash Collection Routes API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
