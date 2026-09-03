# Test Scripts

This directory contains ad-hoc test and debug scripts for development and troubleshooting.

## Test Files

### OpenAI Integration Tests

- **`test_openai_minimal.py`** - Minimal test of the OpenAI SDK to verify API key and basic connectivity
- **`test_openai_client.py`** - Test the OpenAI (GPT-5-nano) client with sample user data
- **`test_full_user_analysis.py`** - End-to-end test of user analysis pipeline
- **`test_user_analyzer_debug.py`** - Debug script to troubleshoot user analyzer issues

### Backend/API Tests

- **`test-recommendation.js`** - End-to-end test of recommendation flow (rec-engine + backend tRPC)

## Running Tests

All tests should be run from the repository root with the virtual environment activated:

```bash
# From repository root
cd "$(git rev-parse --show-toplevel)"
source venv/bin/activate

# Run Python tests
python3 scripts/tests/test_openai_minimal.py
python3 scripts/tests/test_openai_client.py
python3 scripts/tests/test_full_user_analysis.py
python3 scripts/tests/test_user_analyzer_debug.py

# Run Node.js tests (requires backend and rec-engine running)
node scripts/tests/test-recommendation.js
```

## Prerequisites

- Virtual environment activated
- `.env` file configured with required credentials (OPENAI_API_KEY, SUPABASE credentials, etc.)
- Database migrations run (see `apps/shared/migrations/`)

## Notes

These are development/debug scripts, not production tests. The pytest suite lives in `scripts/legacy-ingestion/tests/`; the `apps/*` Python services have no unit tests. TypeScript tests are Vitest `*.test.ts` files beside the code in `apps/api` and `apps/frontend`.
