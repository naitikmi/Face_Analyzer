"""
FastAPI application entry point.

Run with: uvicorn face_analyzer.api.app:app --reload --port 8000
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from face_analyzer.api.routes.analyze import router as analyze_router

# Comma-separated list of allowed frontend origins. Defaults to the Next.js
# dev server; set ALLOWED_ORIGINS in production to the deployed frontend URL.
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app = FastAPI(title="Face Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
