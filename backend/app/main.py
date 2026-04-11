"""
CodeGalaxy Backend - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
import os
# Force Numba cache to writable data volume before any other imports
os.environ["NUMBA_CACHE_DIR"] = "/app/data/numba_cache"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.database import init_db
from app.routers import ingest, repos, files


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="CodeGalaxy API",
    description="3D repository visualization backend — ingestion, parsing, embedding & analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(repos.router)
app.include_router(files.router)


@app.get("/")
async def root():
    return {
        "name": "CodeGalaxy API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
@app.get("/ping")
async def health():
    return {"status": "Stellar engine active"}
