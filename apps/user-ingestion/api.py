#!/usr/bin/env python3
"""
FastAPI service for user demographics ingestion.

This service exposes HTTP endpoints for:
- Health checks
- Manual trigger of user analysis
- Status queries
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from user_analyzer import RedditUserAnalyzer
from shared.config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="WhichGLP User Ingestion API",
    version="0.1.0",
    description="Demographics extraction service for Reddit users"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class AnalyzeRequest(BaseModel):
    limit: Optional[int] = 10
    rate_limit_delay: float = 2.0


class AnalyzeResponse(BaseModel):
    status: str
    message: str


class StatsResponse(BaseModel):
    total_users: int
    unanalyzed_users: int


# Background task tracker
_analysis_running = False


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway/load balancers."""
    return {
        "status": "healthy",
        "service": "user-ingestion",
        "version": "0.1.0"
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get statistics about analyzed vs unanalyzed users."""
    try:
        analyzer = RedditUserAnalyzer()

        # Get total users
        with analyzer.db.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(DISTINCT author) FROM reddit_posts WHERE author IS NOT NULL AND author != '[deleted]'")
            total_users = cursor.fetchone()[0]

        # Get unanalyzed users
        unanalyzed = analyzer.get_unanalyzed_usernames()

        return {
            "total_users": total_users,
            "unanalyzed_users": len(unanalyzed)
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def trigger_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger user demographics analysis.

    This runs the analysis in the background and returns immediately.
    """
    global _analysis_running

    if _analysis_running:
        raise HTTPException(
            status_code=409,
            detail="Analysis already running. Please wait for it to complete."
        )

    try:
        # Run analysis in background
        def run_analysis():
            global _analysis_running
            _analysis_running = True
            try:
                analyzer = RedditUserAnalyzer()
                analyzer.run(
                    limit=request.limit,
                    rate_limit_delay=request.rate_limit_delay
                )
            finally:
                _analysis_running = False

        background_tasks.add_task(run_analysis)

        return {
            "status": "started",
            "message": f"Analysis started for up to {request.limit or 'all'} users"
        }

    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """Get current analysis status."""
    return {
        "analysis_running": _analysis_running
    }


if __name__ == "__main__":
    import uvicorn

    # Railway sets PORT env var, fall back to 8002 for local dev
    port = int(os.getenv("PORT", "8002"))

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
