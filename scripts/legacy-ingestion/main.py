"""
FastAPI server for data ingestion and extraction services.
Provides HTTP endpoints to trigger Reddit ingestion and AI extraction tasks.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime

# Import ingestion modules
from ingestion.historical_ingest import run_historical_ingestion
from extraction.ai_extraction import run_extraction

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhichGLP Data Ingestion API",
    description="API for triggering Reddit data ingestion and AI extraction",
    version="0.1.0"
)

# Request models
class IngestRequest(BaseModel):
    """Request model for historical ingestion."""
    subreddit: str
    posts: int = 100
    comments: int = 20

class ExtractionRequest(BaseModel):
    """Request model for AI extraction."""
    subreddit: str
    posts_only: bool = True
    limit: Optional[int] = None
    dry_run: bool = False

# Task status tracking (simple in-memory store)
tasks = {}

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "WhichGLP Data Ingestion",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    """Health check for Railway."""
    return {"status": "healthy"}

@app.post("/ingest")
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger historical Reddit ingestion for a subreddit.

    Args:
        subreddit: Subreddit name (e.g., 'Ozempic')
        posts: Number of top posts to fetch (default: 100)
        comments: Number of comments per post (default: 20)

    Returns:
        Task ID for tracking progress
    """
    task_id = f"ingest_{request.subreddit}_{datetime.utcnow().timestamp()}"

    logger.info(f"Starting ingestion task {task_id} for r/{request.subreddit}")

    # Add task to background
    background_tasks.add_task(
        run_ingestion_task,
        task_id,
        request.subreddit,
        request.posts,
        request.comments
    )

    tasks[task_id] = {
        "status": "running",
        "subreddit": request.subreddit,
        "started_at": datetime.utcnow().isoformat()
    }

    return {
        "task_id": task_id,
        "status": "started",
        "subreddit": request.subreddit
    }

@app.post("/extract")
async def trigger_extraction(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """
    Trigger AI extraction for a subreddit.

    Args:
        subreddit: Subreddit name (e.g., 'Ozempic')
        posts_only: Only extract from posts (faster, default: True)
        limit: Limit number of items to process (optional)
        dry_run: Test without database writes (default: False)

    Returns:
        Task ID for tracking progress
    """
    task_id = f"extract_{request.subreddit}_{datetime.utcnow().timestamp()}"

    logger.info(f"Starting extraction task {task_id} for r/{request.subreddit}")

    # Add task to background
    background_tasks.add_task(
        run_extraction_task,
        task_id,
        request.subreddit,
        request.posts_only,
        request.limit,
        request.dry_run
    )

    tasks[task_id] = {
        "status": "running",
        "subreddit": request.subreddit,
        "started_at": datetime.utcnow().isoformat()
    }

    return {
        "task_id": task_id,
        "status": "started",
        "subreddit": request.subreddit
    }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a background task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return tasks[task_id]

@app.get("/tasks")
async def list_tasks():
    """List all tasks."""
    return {"tasks": tasks}

# Background task functions
async def run_ingestion_task(task_id: str, subreddit: str, posts: int, comments: int):
    """Run historical ingestion in background."""
    try:
        logger.info(f"Running ingestion for r/{subreddit}")

        # Call the ingestion function
        result = run_historical_ingestion(
            subreddit=subreddit,
            num_posts=posts,
            comments_per_post=comments
        )

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
        tasks[task_id]["result"] = result

        logger.info(f"Ingestion task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Ingestion task {task_id} failed: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["failed_at"] = datetime.utcnow().isoformat()

async def run_extraction_task(
    task_id: str,
    subreddit: str,
    posts_only: bool,
    limit: Optional[int],
    dry_run: bool
):
    """Run AI extraction in background."""
    try:
        logger.info(f"Running extraction for r/{subreddit}")

        # Call the extraction function
        result = run_extraction(
            subreddit=subreddit,
            posts_only=posts_only,
            limit=limit,
            dry_run=dry_run
        )

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
        tasks[task_id]["result"] = result

        logger.info(f"Extraction task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Extraction task {task_id} failed: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["failed_at"] = datetime.utcnow().isoformat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
