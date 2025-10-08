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
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from user_analyzer import RedditUserAnalyzer
from shared.config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="WhichGLP User Extraction API",
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

# Startup/shutdown event handlers
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 USER EXTRACTION SERVICE STARTING UP")
    logger.info(f"   Service: user-extraction")
    logger.info(f"   Port: {os.getenv('PORT', '8002')}")
    logger.info(f"   Model: GLM-4.5-Air")
    logger.info(f"   Time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("🛑 USER EXTRACTION SERVICE SHUTTING DOWN")
    logger.info(f"   Time: {datetime.now().isoformat()}")
    logger.info("=" * 80)


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
        "service": "user-extraction",
        "version": "0.1.0"
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get statistics about analyzed vs unanalyzed users."""
    try:
        analyzer = RedditUserAnalyzer()

        # Get total users using Supabase client
        # Count distinct authors from posts that have been AI-extracted
        # Need to join extracted_features with reddit_posts to get author (ef doesn't have author column)
        response = analyzer.db.client.table('extracted_features').select('post_id').execute()
        extracted_post_ids = {feature['post_id'] for feature in (response.data if response.data else [])}

        # Get authors for these posts
        posts_response = analyzer.db.client.table('reddit_posts').select('author').in_('post_id', list(extracted_post_ids)).execute()
        unique_authors = {post['author'] for post in (posts_response.data if posts_response.data else [])
                         if post['author'] and post['author'] != '[deleted]' and post['author'] != 'AutoModerator'}
        total_users = len(unique_authors)

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

    logger.info("=" * 80)
    logger.info("📥 USER ANALYSIS REQUEST RECEIVED")
    logger.info(f"   Limit: {request.limit or 'all users'}")
    logger.info(f"   Rate limit delay: {request.rate_limit_delay}s")
    logger.info("=" * 80)

    if _analysis_running:
        logger.warning("⚠️  Analysis already running - request rejected")
        raise HTTPException(
            status_code=409,
            detail="Analysis already running. Please wait for it to complete."
        )

    try:
        # Run analysis in background
        def run_analysis():
            global _analysis_running
            _analysis_running = True
            start_time = datetime.now()

            try:
                logger.info("🔧 Initializing user analyzer...")
                analyzer = RedditUserAnalyzer()
                logger.info("✅ User analyzer initialized")

                logger.info(f"🎯 Starting user analysis (limit: {request.limit or 'none'})...")
                analyzer.run(
                    limit=request.limit,
                    rate_limit_delay=request.rate_limit_delay
                )

                duration = (datetime.now() - start_time).total_seconds()
                logger.info("=" * 80)
                logger.info("✨ USER ANALYSIS BATCH COMPLETED")
                logger.info(f"   Duration: {duration:.2f}s")
                logger.info("=" * 80)

            except Exception as e:
                logger.error("=" * 80)
                logger.error("💥 USER ANALYSIS FATAL ERROR")
                logger.error(f"   Error type: {type(e).__name__}")
                logger.error(f"   Error message: {str(e)}")
                logger.error("=" * 80)
                logger.exception("Full traceback:")
            finally:
                _analysis_running = False
                logger.info("🏁 Analysis task completed, worker released")

        background_tasks.add_task(run_analysis)
        logger.info("✅ Analysis task queued successfully")

        return {
            "status": "started",
            "message": f"Analysis started for up to {request.limit or 'all'} users"
        }

    except Exception as e:
        logger.error(f"❌ Failed to start analysis: {str(e)}", exc_info=True)
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
