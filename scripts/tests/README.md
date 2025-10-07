# Test Scripts

This directory contains ad-hoc test and debug scripts for development and troubleshooting.

## Test Files

### GLM Integration Tests

- **`test_zai_minimal.py`** - Minimal test of ZAI SDK to verify API key and basic connectivity
- **`test_glm.py`** - Test GLM client with sample user data
- **`test_full_user_analysis.py`** - End-to-end test of user analysis pipeline
- **`test_user_analyzer_debug.py`** - Debug script to troubleshoot user analyzer issues

## Running Tests

All tests should be run from the repository root with the virtual environment activated:

```bash
# From repository root
cd /Users/bryan/Github/which-glp
source venv/bin/activate

# Run individual tests
python3 scripts/tests/test_zai_minimal.py
python3 scripts/tests/test_glm.py
python3 scripts/tests/test_full_user_analysis.py
python3 scripts/tests/test_user_analyzer_debug.py
```

## Prerequisites

- Virtual environment activated
- `.env` file configured with required credentials (GLM_API_KEY, SUPABASE credentials, etc.)
- Database migrations run (see `apps/shared/migrations/`)

## Notes

These are development/debug scripts, not production tests. For proper unit tests, see:
- `apps/user-ingestion/tests/`
- `apps/post-ingestion/tests/`
- `apps/post-extraction/tests/`
- `scripts/legacy-ingestion/tests/`
