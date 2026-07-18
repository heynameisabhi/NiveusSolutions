"""
Veritas Claims Analytics — FastAPI Entry Point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from src.database.engine import engine, Base
from src.api.routes import router
from src.models import models  # noqa: F401 — ensures models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=os.getenv("APP_NAME", "Veritas Claims Analytics"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="Medical data standardization pipeline with operational dashboard.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": os.getenv("APP_NAME", "Veritas Claims Analytics"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "docs": "/docs",
    }
