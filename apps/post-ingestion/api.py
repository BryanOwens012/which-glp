#!/usr/bin/env python3
"""FastAPI service for post ingestion."""

import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recent_ingest import ingest_recent_posts, ingest_multiple_subreddits, TIER1_SUBREDDITS
from shared.config import get_logger

logger = get_logger(__name__)

app = FastAPI(title="WhichGLP Post Ingestion API", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Startup/shutdown event handlers
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 POST INGESTION SERVICE STARTING UP")
    logger.info(f"   Service: post-ingestion")
    logger.info(f"   Port: {os.getenv('PORT', '8003')}")
    logger.info(f"   Tier 1 subreddits: {', '.join(TIER1_SUBREDDITS)}")
    logger.info(f"   Time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("🛑 POST INGESTION SERVICE SHUTTING DOWN")
    logger.info(f"   Time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

class IngestRequest(BaseModel):
    subreddit: Optional[str] = None
    posts_limit: int = 100
    tier1: bool = False

_ingestion_running = False

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "post-ingestion"}

@app.post("/api/ingest")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    global _ingestion_running

    logger.info("=" * 80)
    logger.info("📥 INGESTION REQUEST RECEIVED")
    logger.info(f"   Tier 1 mode: {request.tier1}")
    if request.tier1:
        logger.info(f"   Subreddits: {', '.join(TIER1_SUBREDDITS)}")
    else:
        logger.info(f"   Subreddit: {request.subreddit or 'none specified'}")
    logger.info(f"   Posts limit: {request.posts_limit}")
    logger.info("=" * 80)

    if _ingestion_running:
        logger.warning("⚠️  Ingestion already running - request rejected")
        raise HTTPException(status_code=409, detail="Ingestion already running")

    def run_ingestion():
        global _ingestion_running
        _ingestion_running = True
        start_time = datetime.now()

        try:
            if request.tier1:
                logger.info(f"🎯 Starting Tier 1 ingestion for {len(TIER1_SUBREDDITS)} subreddits...")
                logger.info(f"   Subreddits: {', '.join(TIER1_SUBREDDITS)}")
                result = ingest_multiple_subreddits(TIER1_SUBREDDITS, request.posts_limit)
                logger.info("=" * 80)
                logger.info("✨ TIER 1 INGESTION COMPLETED")
                logger.info(f"   Subreddits processed: {len(TIER1_SUBREDDITS)}")
                logger.info(f"   Duration: {(datetime.now() - start_time).total_seconds():.2f}s")
                logger.info("=" * 80)
            elif request.subreddit:
                logger.info(f"🎯 Starting ingestion for r/{request.subreddit}...")
                result = ingest_recent_posts(request.subreddit, request.posts_limit)
                logger.info("=" * 80)
                logger.info("✨ INGESTION COMPLETED")
                logger.info(f"   Subreddit: r/{request.subreddit}")
                logger.info(f"   Duration: {(datetime.now() - start_time).total_seconds():.2f}s")
                logger.info("=" * 80)
            else:
                logger.error("❌ No subreddit specified and tier1=False")

        except Exception as e:
            logger.error("=" * 80)
            logger.error("💥 INGESTION PIPELINE FATAL ERROR")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            logger.error("=" * 80)
            logger.exception("Full traceback:")
        finally:
            _ingestion_running = False
            logger.info("🏁 Ingestion task completed, worker released")

    background_tasks.add_task(run_ingestion)
    logger.info("✅ Ingestion task queued successfully")
    return {"status": "started", "message": f"Ingestion started"}

@app.get("/api/status")
async def get_status():
    return {"ingestion_running": _ingestion_running}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
