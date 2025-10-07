#!/usr/bin/env python3
"""FastAPI service for post ingestion."""

import os
import sys
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from recent_ingest import ingest_recent_posts, ingest_multiple_subreddits, TIER1_SUBREDDITS
from shared.config import get_logger

logger = get_logger(__name__)

app = FastAPI(title="WhichGLP Post Ingestion API", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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
    if _ingestion_running:
        raise HTTPException(status_code=409, detail="Ingestion already running")

    def run_ingestion():
        global _ingestion_running
        _ingestion_running = True
        try:
            if request.tier1:
                ingest_multiple_subreddits(TIER1_SUBREDDITS, request.posts_limit)
            elif request.subreddit:
                ingest_recent_posts(request.subreddit, request.posts_limit)
        finally:
            _ingestion_running = False

    background_tasks.add_task(run_ingestion)
    return {"status": "started", "message": f"Ingestion started"}

@app.get("/api/status")
async def get_status():
    return {"ingestion_running": _ingestion_running}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
