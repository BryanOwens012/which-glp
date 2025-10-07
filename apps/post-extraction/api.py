#!/usr/bin/env python3
"""FastAPI service for post extraction using GLM-4.5-Air (replaces Claude)."""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the extraction pipeline - reuses most code from data-ingestion
# Just swaps out the AI client from Claude to GLM
from glm_client import get_client
from shared.config import get_logger

logger = get_logger(__name__)

app = FastAPI(title="WhichGLP Post Extraction API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ExtractionRequest(BaseModel):
    subreddit: str | None = None
    limit: int | None = None
    posts_only: bool = True

_extraction_running = False

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "post-extraction", "model": "glm-4.5-air"}

@app.post("/api/extract")
async def trigger_extraction(request: ExtractionRequest, background_tasks: BackgroundTasks):
    global _extraction_running
    if _extraction_running:
        raise HTTPException(status_code=409, detail="Extraction already running")

    def run_extraction():
        global _extraction_running
        _extraction_running = True
        try:
            # Import here to avoid circular dependencies
            from shared.database import DatabaseManager
            from prompts import build_post_prompt
            from filters import should_process_post

            db = DatabaseManager()
            glm = get_client()

            # Query unprocessed posts
            query = """
                SELECT post_id, title, body, subreddit, author_flair_text
                FROM reddit_posts
                WHERE post_id NOT IN (SELECT post_id FROM extracted_features WHERE post_id IS NOT NULL)
            """
            if request.subreddit:
                query += f" AND subreddit = '{request.subreddit}'"
            query += " ORDER BY created_at DESC"
            if request.limit:
                query += f" LIMIT {request.limit}"

            with db.conn.cursor() as cursor:
                cursor.execute(query)
                posts = cursor.fetchall()

            logger.info(f"Found {len(posts)} unprocessed posts")

            # Process each post (simplified - full logic would use extraction pipeline)
            for post_id, title, body, subreddit, flair in posts:
                try:
                    if not should_process_post((post_id, title, body, subreddit, flair), subreddit):
                        continue

                    prompt = build_post_prompt(title, body or "", flair or "")
                    features, metadata = glm.extract_features(prompt)

                    logger.info(f"✓ Extracted {post_id} - Cost: ${metadata['cost_usd']:.6f}")
                    # Insert to database (simplified)
                    # Full implementation would use same insert logic as data-ingestion/extraction
                except Exception as e:
                    logger.error(f"Failed to extract {post_id}: {e}")

            db.close()
        finally:
            _extraction_running = False

    background_tasks.add_task(run_extraction)
    return {"status": "started", "message": f"Extraction started with GLM-4.5-Air"}

@app.get("/api/status")
async def get_status():
    return {"extraction_running": _extraction_running}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8004"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
