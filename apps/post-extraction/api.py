#!/usr/bin/env python3
"""FastAPI service for post extraction using GLM-4.5-Air (replaces Claude)."""

import os
import sys
from pathlib import Path
from datetime import datetime
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

# Startup/shutdown event handlers
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 POST EXTRACTION SERVICE STARTING UP")
    logger.info(f"   Service: post-extraction")
    logger.info(f"   Model: GLM-4.5-Air")
    logger.info(f"   Port: {os.getenv('PORT', '8004')}")
    logger.info(f"   Time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("🛑 POST EXTRACTION SERVICE SHUTTING DOWN")
    logger.info(f"   Time: {datetime.now().isoformat()}")
    logger.info("=" * 80)

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

    logger.info("=" * 80)
    logger.info("📥 EXTRACTION REQUEST RECEIVED")
    logger.info(f"   Subreddit: {request.subreddit or 'all'}")
    logger.info(f"   Limit: {request.limit or 'none'}")
    logger.info(f"   Posts only: {request.posts_only}")
    logger.info("=" * 80)

    if _extraction_running:
        logger.warning("⚠️  Extraction already running - request rejected")
        raise HTTPException(status_code=409, detail="Extraction already running")

    def run_extraction():
        global _extraction_running
        _extraction_running = True
        start_time = datetime.now()
        processed = 0
        failed = 0
        skipped = 0
        total_cost = 0.0

        try:
            logger.info("🔧 Initializing extraction pipeline...")

            # Import here to avoid circular dependencies
            from shared.database import DatabaseManager
            from prompts import build_post_prompt
            from filters import should_process_post

            db = DatabaseManager()
            logger.info("✅ Database connection established")

            glm = get_client()
            logger.info("✅ GLM client initialized")

            # Query unprocessed posts using PostgreSQL function with LEFT JOIN
            # This performs all filtering at the database level - most efficient approach
            logger.info("🔍 Querying unprocessed posts from database...")

            # Call PostgreSQL function that performs LEFT JOIN filtering
            # Function: get_unprocessed_posts(subreddit, limit)
            # SQL: SELECT p.* FROM reddit_posts p
            #      LEFT JOIN extracted_features ef ON p.post_id = ef.post_id
            #      WHERE ef.post_id IS NULL
            response = db.client.rpc('get_unprocessed_posts', {
                'p_subreddit': request.subreddit,
                'p_limit': request.limit
            }).execute()

            all_posts = response.data if response.data else []

            # Convert to tuple format for processing
            posts = [(p['post_id'], p['title'], p['body'], p['subreddit'], p['author_flair_text'])
                     for p in all_posts]

            logger.info(f"📊 Found {len(posts)} unprocessed posts")

            # Process each post (simplified - full logic would use extraction pipeline)
            for i, (post_id, title, body, subreddit, flair) in enumerate(posts, 1):
                try:
                    logger.info(f"📝 Processing post {i}/{len(posts)}: {post_id} from r/{subreddit}")

                    if not should_process_post((post_id, title, body, subreddit, flair), subreddit):
                        logger.info(f"⏭️  Skipping post {post_id} (filtered out)")
                        skipped += 1
                        continue

                    prompt = build_post_prompt(title, body or "", flair or "")
                    logger.debug(f"🤖 Sending to GLM for extraction: {post_id}")

                    features, metadata = glm.extract_features(prompt)

                    cost = metadata.get('cost_usd', 0)
                    total_cost += cost

                    # Prepare data for database insertion
                    feature_data = {
                        'post_id': post_id,
                        'comment_id': None,
                        'summary': features.summary,
                        'beginning_weight': features.beginning_weight.model_dump() if features.beginning_weight else None,
                        'end_weight': features.end_weight.model_dump() if features.end_weight else None,
                        'duration_weeks': features.duration_weeks,
                        'cost_per_month': features.cost_per_month,
                        'currency': features.currency,
                        'drugs_mentioned': features.drugs_mentioned,
                        'primary_drug': features.primary_drug,
                        'drug_sentiments': features.drug_sentiments,
                        'sentiment_pre': features.sentiment_pre,
                        'sentiment_post': features.sentiment_post,
                        'has_insurance': features.has_insurance,
                        'insurance_provider': features.insurance_provider,
                        'comorbidities': features.comorbidities,
                        'location': features.location,
                        'age': features.age,
                        'sex': features.sex,
                        'state': features.state,
                        'country': features.country,
                        'model_used': metadata.get('model'),
                        'confidence_score': features.confidence_score,
                        'processing_cost_usd': cost,
                        'tokens_input': metadata.get('tokens_input'),
                        'tokens_output': metadata.get('tokens_output'),
                        'processing_time_ms': metadata.get('processing_time_ms'),
                        'processed_at': datetime.now().isoformat(),  # Supabase client handles datetime serialization
                        'raw_response': metadata.get('raw_response'),
                        'side_effects': [se.model_dump() for se in features.side_effects] if features.side_effects else [],
                        'dosage_progression': features.dosage_progression,
                        'exercise_frequency': features.exercise_frequency,
                        'dietary_changes': features.dietary_changes,
                        'previous_weight_loss_attempts': features.previous_weight_loss_attempts,
                        'drug_source': features.drug_source,
                        'switching_drugs': features.switching_drugs,
                        'side_effect_timing': features.side_effect_timing,
                        'food_intolerances': features.food_intolerances,
                        'plateau_mentioned': features.plateau_mentioned,
                        'rebound_weight_gain': features.rebound_weight_gain,
                        'labs_improvement': features.labs_improvement,
                        'medication_reduction': features.medication_reduction,
                        'nsv_mentioned': features.nsv_mentioned,
                        'support_system': features.support_system,
                        'pharmacy_access_issues': features.pharmacy_access_issues,
                        'mental_health_impact': features.mental_health_impact,
                        'side_effect_resolution': features.side_effect_resolution,
                        'recommendation_score': features.recommendation_score,
                    }

                    # Insert to database
                    try:
                        db.client.table('extracted_features').upsert(
                            feature_data,
                            on_conflict='post_id'
                        ).execute()
                        logger.info(f"✅ Extracted & saved {post_id} - Cost: ${cost:.6f}, Total cost: ${total_cost:.6f}")
                        processed += 1
                    except Exception as insert_error:
                        logger.error(f"❌ Failed to insert {post_id} to database: {insert_error}")
                        failed += 1

                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Failed to extract {post_id}: {str(e)}", exc_info=True)

            db.close()
            logger.info("🔌 Database connection closed")

            # Final summary
            duration = (datetime.now() - start_time).total_seconds()
            logger.info("=" * 80)
            logger.info("✨ EXTRACTION BATCH COMPLETED")
            logger.info(f"   Total posts: {len(posts)}")
            logger.info(f"   Processed: {processed}")
            logger.info(f"   Failed: {failed}")
            logger.info(f"   Skipped: {skipped}")
            logger.info(f"   Total cost: ${total_cost:.6f}")
            logger.info(f"   Duration: {duration:.2f}s")
            logger.info("=" * 80)

        except Exception as e:
            logger.error("=" * 80)
            logger.error("💥 EXTRACTION PIPELINE FATAL ERROR")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Error message: {str(e)}")
            logger.error(f"   Processed before error: {processed}")
            logger.error(f"   Failed before error: {failed}")
            logger.error("=" * 80)
            logger.exception("Full traceback:")
        finally:
            _extraction_running = False
            logger.info("🏁 Extraction task completed, worker released")

    background_tasks.add_task(run_extraction)
    logger.info("✅ Extraction task queued successfully")
    return {"status": "started", "message": f"Extraction started with GLM-4.5-Air"}

@app.get("/api/status")
async def get_status():
    return {"extraction_running": _extraction_running}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8004"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
