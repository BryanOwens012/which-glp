# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WhichGLP is a GLP-1 weight-loss drug comparison platform that aggregates real-world user experiences from Reddit to help people make informed medication decisions. The project uses AI extraction (GPT-5-nano) to structure unstructured social media data into a searchable database.

**Mission**: Build a proprietary dataset of GLP-1 outcomes that generic LLMs cannot provide (location-specific pricing, personalized predictions, insurance coverage patterns).

## Security Posture

- **Least privilege (tightest scope)**: always keep security to the tightest (minimal scope) possible that still accomplishes all our goals. Grant exactly the access needed and nothing more. This applies to Supabase RLS/policies, GRANTs, and roles, as well as to code (API surface, permissions, env access, etc.).
- **Fail-closed, not fail-open**: when an error or uncertainty occurs, the default must be to **block** access rather than grant it. Never let a failure path fall through to allowing an action; on any error, deny.

## Tools, CLIs & MCP Servers (Be Liberal)

Be liberal with calling tools, CLI commands, and MCP servers to make changes and to diagnose and solve problems — particularly when diagnosing build or deploy failures.

- **Reach for the platform's MCP server / CLI.** This repo uses **Railway** (backend services + Redis), **Vercel** (frontend), and **Supabase** (PostgreSQL) — install and use their MCP servers/CLIs (and analogously for Figma, Framer, AWS, GCP, Azure, Datadog, etc. if they come into play).
- **Destructive actions still require approval.** Be liberal with read-only, diagnostic, and safely reversible actions — but always ask for the user's approval before executing destructive actions (deletes, rollbacks, production config/env changes, force operations, etc.).
- **Suggest `/goal` for goal-driven runs.** When a task should run until done (e.g., fully fixing a deploy failure), suggest that the user can give the `/goal` slash-command to command you to keep working until the goal is reached.

## LLM Model Selection

When writing or reviewing code that calls an LLM — or when the user asks which model to use — never default to a single "best practice" model without thinking through the specific usage. The right model/reasoning combo depends on several factors, and the optimal choice is often not the obvious default. Always **present the user with options and tradeoffs** rather than silently picking one.

**Factors to reason through:**

- **Who uses this call?** A background batch job (no human waiting) tolerates higher latency and can use a larger model for accuracy. A customer-facing feature needs fast time-to-first-token and should prefer a lighter model or adaptive reasoning.
- **Latency requirements.** Streaming to a live user? Minimize TTFT — prefer smaller models, `effort: 'low'` or `'medium'`, and skip thinking on simple paths (`thinking: { type: 'adaptive' }`). Asynchronous enrichment pipeline? Latency doesn't matter; accuracy does.
- **Accuracy and reasoning needs.** Simple classification, extraction, or slot-filling → smaller/faster model (e.g. Haiku, GPT-5-nano). Multi-step reasoning, SQL generation, complex analysis → a reasoning-capable model at the appropriate effort level. Don't pay for reasoning on calls that don't need it; don't skimp on it for calls that do.
- **Tool use.** Heavy agentic tool loops (multiple round-trips, SQL generation, web search) benefit from reasoning. Single-tool structured-extraction calls usually don't.
- **Context length.** Does the call need long-context (large documents, long conversation history)? Some models handle this better or more cheaply than others.
- **Cost.** A call made once per user action has a different cost profile than one made per row in a 100k-row enrichment job (e.g. the extraction pipeline). Match the model tier to the volume and business value.

**Reasoning / thinking / effort knobs (Anthropic):**

| Setting | When to use |
|---|---|
| No thinking (default) | Fast, simple calls — classification, slot-fill, short generation |
| `thinking: { type: 'adaptive' }` | Mixed workloads — simple queries skip thinking, hard ones use it; minimal TTFT penalty |
| `thinking: { type: 'enabled' }` | Always reason — analytics, complex SQL, multi-hop questions |
| `effort: 'low'` | Latency-critical, low-complexity |
| `effort: 'medium'` | Balanced; good default for interactive tool-use calls |
| `effort: 'high'` (default) | High-stakes, slow-path, or batch accuracy work |

Present these options explicitly when a model choice is ambiguous. The best combo is sometimes counterintuitive — e.g., a smaller model with full thinking can outperform a larger model without it on reasoning tasks, at lower cost and similar latency.

## LLM Calls (Prompt Caching & Observability)

### Aggressive Prompt Caching + Cache Pre-Warming

For **all LLM calls, regardless of provider**, always look for opportunities to implement aggressive prompt caching and to pre-warm the cache so it is always hot when real requests arrive. Prompt caching is a near-free win: cached input tokens are ~50–90% cheaper depending on provider, and time-to-first-token drops by up to ~80%. Pre-warming ensures bursty or low-traffic workloads don't pay cold-cache prices — the warmer keeps the cache alive between real requests. In this repo that especially means the **GPT-5-nano extraction services** (`apps/post-extraction`, `apps/user-extraction`): structure prompts so the static parts (system prompt, extraction instructions, schemas, few-shot examples) form a byte-stable prefix and the volatile parts (the Reddit post/comment being extracted) come last. OpenAI caches automatically for prompts ≥1024 tokens, but only if the prefix is byte-identical across requests — never interpolate timestamps/IDs into the static prefix, and verify hits via `usage.prompt_tokens_details.cached_tokens`. Provider caching APIs and best practices evolve — search the internet for the provider's current prompt-caching docs when implementing or reviewing.

### Langfuse (Tracing Yes, Prompts No)

If this repo adopts Langfuse, then:

- **All LLM calls must be recorded through Langfuse tracing and sessions**, so cost, latency, and behavior are observable per conversation/run.
- **Do not store LLM prompts in Langfuse** (no prompt management / `getPrompt()`). Prompts live **in the codebase** (e.g. `apps/post-extraction/prompts.py`, `apps/user-extraction/prompts.py`) as the single source of truth — version-controlled with the code that uses them, and easily readable as context by terminal agents like Claude Code.

## Documentation Structure

This project uses multiple documentation files located in the `docs/` directory:

- **CLAUDE.md** (this file) - Technical development guide for Claude Code
- **docs/AGENTS.md** - **IMPORTANT**: Primary instructions, business context, development process, and coding standards
- **docs/AGENTS_APPENDLOG.md** - **IMPORTANT**: Historical changelog of all development work (append-only log)
- **docs/TECH_SPEC.md** - Drugs, data sources, tech stack, pipelines
- **docs/MONETIZATION.md** (private, not committed) - Business strategy and revenue models
- **docs/ARCHITECTURE.md** - System architecture and service design
- **docs/DEPLOYMENT_SUMMARY.md** - Deployment summary and migration notes
- **docs/RAILWAY_SETUP.md** - Railway deployment instructions
- **docs/BACKEND_AND_TRPC_SETUP.md** - Backend and tRPC setup guide
- **docs/BACKEND_IMPLEMENTATION_PLAN.md** - Backend implementation plan

**Key Files for Claude Code:**
- Read **docs/AGENTS.md** for development workflow, coding standards, and project guidelines
- Read **docs/AGENTS_APPENDLOG.md** to understand the history of development changes
- Consult **docs/TECH_SPEC.md** for technical specifications and drug catalog
- Reference **docs/ARCHITECTURE.md** for system design and service architecture

When working on tasks, check the `docs/` directory for relevant documentation before making changes.

## Monorepo Structure

This is a monorepo with the following structure:

```
/                           # Repository root
├── .env                    # Environment variables (git-ignored)
├── requirements.txt        # Python dependencies (monorepo-wide)
├── venv/                   # Python virtual environment
├── docs/                   # Documentation
│   ├── AGENTS.md          # Primary instructions and business context
│   ├── TECH_SPEC.md       # Technical specifications
│   ├── ARCHITECTURE.md    # System architecture
│   ├── DEPLOYMENT_SUMMARY.md
│   └── RAILWAY_SETUP.md
├── apps/                   # Railway-deployed services
│   ├── frontend/          # Next.js 15 frontend
│   ├── api/               # Node.js tRPC API
│   ├── rec-engine/        # FastAPI recommendation engine
│   ├── user-extraction/   # User demographics extraction service
│   ├── post-ingestion/    # Reddit post fetching service
│   ├── post-extraction/   # GPT-5-nano-based feature extraction service
│   └── shared/            # Shared database migrations and utilities
├── scripts/               # One-off scripts, tests, analysis, legacy code
│   ├── legacy-ingestion/  # Old Claude-based ingestion (deprecated)
│   ├── tests/             # Ad-hoc test and debug scripts
│   └── analysis/          # Data analysis notebooks and scripts
│       ├── notebooks/     # Jupyter notebooks
│       ├── scripts/       # Analysis Python scripts
│       └── outputs/       # Generated analysis outputs
└── backups/               # Local backup storage (referenced by shared.config)
    ├── ingestion/         # Reddit API ingestion backups
    └── extraction/        # AI extraction backups
```

**Critical**: All Python commands must be run from the repository root (`/`) with the virtual environment activated. All git operations run from the root.

## Environment Setup

### Python Virtual Environment

The project uses a virtual environment at `/venv/`:

```bash
# From repository root
source venv/bin/activate
pip3 install -r requirements.txt
pip3 install -e scripts/legacy-ingestion  # Install as editable package
```

### Required Environment Variables

Create `.env` in the repository root:

```bash
# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-db-password

# Reddit API (OAuth 2.0)
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=whichglp-ingestion/0.1

# Anthropic (for AI extraction)
ANTHROPIC_API_KEY=your-api-key
```

**Database Connection**: The code extracts the project reference from `SUPABASE_URL` and constructs the PostgreSQL connection string automatically. See `scripts/legacy-ingestion/shared/database.py` for implementation.

## Data Ingestion Architecture

### Package Structure

The data-ingestion app is installed as an editable Python package with the namespace `reddit_ingestion`. This means you run modules like:

```bash
python3 -m reddit_ingestion.historical_ingest --subreddit Ozempic
```

**Not** `python3 scripts/legacy-ingestion/ingestion/historical_ingest.py` (old pattern).

### Module Organization

```
scripts/legacy-ingestion/
├── ingestion/              # Reddit API clients and parsers
│   ├── client.py          # PRAW wrapper for Reddit API
│   ├── parser.py          # Parse Reddit JSON into database schema
│   ├── historical_ingest.py  # Batch ingestion script
│   └── upload_from_backup.py  # Upload backup files to Supabase
├── extraction/             # AI-powered feature extraction
│   ├── ai_client.py       # Anthropic Claude API client
│   ├── ai_extraction.py   # Main extraction pipeline
│   ├── context.py         # Build context from posts/comments
│   ├── prompts.py         # Claude prompts for extraction
│   ├── schema.py          # Pydantic models for extracted features
│   └── filters.py         # Determine what to process
├── shared/                 # Shared utilities
│   ├── database.py        # Supabase connection and operations
│   └── config.py          # Logging and monorepo path resolution
├── migrations/             # Database schema migrations
│   ├── run_migration.py   # Migration runner
│   └── *.up.sql / *.down.sql  # Migration files
└── tests/                  # pytest tests
```

### Ingestion Pipeline

**Historical Batch Ingestion** (run once per subreddit):
```bash
# From repository root with venv activated
cd /Users/bryan/Github/which-glp
python3 -m reddit_ingestion.historical_ingest --subreddit Ozempic --posts 100 --comments 20
```

This script:
1. Fetches top 100 posts from the past year using PRAW
2. Fetches top 20 comments per post
3. Parses data using `ingestion/parser.py`
4. Batch inserts to Supabase (100 records per batch with ON CONFLICT for deduplication)
5. Backs up to `scripts/legacy-ingestion/ingestion/backup/historical_run_YYYYMMDD_HHMMSS_{subreddit}/`
6. Creates `summary.json` with statistics

**Backup Upload** (if database insert failed but backup exists):
```bash
python3 -m reddit_ingestion.upload_from_backup /path/to/backup/dir
```

### Database Schema

**Tables** (see `migrations/001_create_reddit_tables.up.sql`):
- `reddit_posts`: Reddit posts with title, selftext, author, created_utc, score, subreddit
- `reddit_comments`: Comments with body, author, created_utc, score, post_id (foreign key)
- `extracted_features`: AI-extracted structured data (drug, weight_loss, cost, side_effects, etc.)

**Key Design Decisions**:
- `post_id` is Reddit's native ID (e.g., `t3_abc123`), stored as TEXT primary key
- `comment_id` is Reddit's native ID (e.g., `t1_xyz789`), stored as TEXT primary key
- Foreign keys enforce referential integrity (comments → posts)
- `ON CONFLICT DO NOTHING` for idempotent batch inserts

## AI Extraction Pipeline

### Extraction Architecture

**Hybrid Approach** (minimize database queries, maximize in-memory processing):
1. **Bulk Export**: Query all unprocessed posts/comments from Supabase into memory
2. **In-Memory Lookup**: Build dictionaries for O(1) context lookup (post → comments, comment → parent comment)
3. **AI Processing**: For each item, build context and send to Claude API
4. **Batch Insert**: Insert extracted features back to Supabase in batches

### Running Extraction

**Posts-only extraction** (faster, for initial dataset build):
```bash
cd /Users/bryan/Github/which-glp
python3 -m extraction.ai_extraction --subreddit Ozempic --posts-only
```

**Full extraction** (posts + comments):
```bash
python3 -m extraction.ai_extraction --subreddit Ozempic
```

**Dry run** (test prompts without database writes):
```bash
python3 -m extraction.ai_extraction --subreddit Ozempic --dry-run --limit 5
```

### Context Building

The extraction pipeline builds rich context for each post/comment to improve AI accuracy:

**For posts**: Include top comments (up to 5)
**For comments**: Include parent post + parent comment chain

This context is passed to Claude via `extraction/prompts.py` to extract structured features like:
- Drug name (Ozempic, Wegovy, Mounjaro, etc.)
- Weight loss amount and timeframe
- Cost (monthly, out-of-pocket, insurance coverage)
- Side effects (nausea, vomiting, fatigue, etc.)
- Demographics (age, sex, starting weight)

### Filtering

Not all posts/comments are processed. See `extraction/filters.py` for logic:
- Posts with <50 characters are skipped (low signal)
- Comments with <30 characters are skipped
- Deleted/removed content is skipped
- Already-processed items are skipped (checks `extracted_features` table)

### Backup Strategy

All AI extractions are backed up to JSON files before database insertion:
- Location: `scripts/legacy-ingestion/extraction_backups/`
- Filename pattern: `extraction_backup_{subreddit}_{timestamp}.json`
- Contains full extraction results + metadata

## Database Migrations

The project uses simple SQL migrations with up/down files:

```bash
cd /Users/bryan/Github/which-glp
python3 apps/shared/migrations/run_migration.py apps/shared/migrations/001_create_reddit_tables.up.sql
```

**Migration Naming Convention**:
- `001_description.up.sql` - Apply migration
- `001_description.down.sql` - Rollback migration

**Migration Files** (run in order):
1. `001_create_reddit_tables` - Create posts and comments tables
2. `002_create_extracted_features` - Create extraction results table
3. `003_add_comprehensive_features` - Add weight, timeframe, side effect columns
4. `004_update_sex_and_resolution` - Update sex enum, add resolution field
5. `005_add_out_of_pocket_drug_source` - Add out_of_pocket_cost and drug_source columns

## Testing

Run tests from the repository root:

```bash
cd /Users/bryan/Github/which-glp
pytest scripts/legacy-ingestion/tests/
pytest scripts/legacy-ingestion/tests/test_parser.py  # Single test file
```

**Test Organization**:
- `test_parser.py` - Test Reddit JSON parsing logic
- `test_integration.py` - Test full ingestion pipeline
- `test_migrations.py` - Test database migrations
- `test_mocks.py` - Test API client mocking

### TypeScript Tests Are Vitest, Named `*.test.ts`

Python is pytest; TypeScript is **Vitest**, in `*.test.ts(x)` files beside the code they
cover. Both `apps/api` and `apps/frontend` run `npm test` (`vitest run`) and
`npm run typecheck`. Never add a second TS runner beside Vitest.

Tests live under `src/`, so `apps/api/tsconfig.json` excludes `**/*.test.ts` to keep them
out of `dist/`; `tsconfig.typecheck.json` adds them back so they are still typechecked.
Anything added to one must stay consistent with the other.

Mock Redis in tests rather than connecting to it — a real connection makes tests
order-dependent and leaks a client per file.

## API HTTP Edge (`apps/api/src/index.ts`)

The tRPC router is wrapped in a hand-rolled Node HTTP handler. Rules for changing it:

- **CORS is an allowlist** in `src/lib/cors.ts`, never a reflection of the `Origin`
  header. An unrecognized origin gets no CORS header. Origin patterns must be anchored at
  both ends, or `https://<allowed-host>.attacker.com` matches.
- **No `Access-Control-Allow-Credentials`.** Nothing here is authenticated. If auth is
  added, add the header and the allowlist becomes load-bearing — revisit both together.
- **Every request body is capped** before buffering (`config.maxRequestBodyBytes`).
  Never accumulate a request stream without a running byte total; `Content-Length` alone
  is absent under chunked encoding and is client-supplied anyway. Do not `req.destroy()`
  to reject: it resets the socket before the 413 reaches the client.
- **Rate limiting lives in Redis, not in process**, because the service runs multiple
  replicas. It fails *open* to a smaller in-process budget when Redis is down — a
  deliberate exception to fail-closed, because this limiter guards availability, not
  access, and failing closed would turn a Redis blip into a site outage. Do not "fix"
  this to fail closed without adding auth first. The Redis client gives up reconnecting
  after three failed attempts, so a replica that loses Redis stays on the in-process
  budget until it restarts.
- **A block covers unknown paths only**, never `/trpc`. Many unrelated users share one
  CGNAT address; blocking the API would lock them all out for an hour.
- **Client IP is the rightmost `X-Forwarded-For` entry** (the one Railway's edge
  appended). The leftmost is attacker-controlled — using it lets any caller pick its own
  rate-limit bucket.
- **Do not log unknown paths per request.** Scanner sprays are most of that traffic; log
  the resulting block instead. Sanitize any attacker-controlled string before logging it.
- **Every new env var is read and validated in `src/lib/config.ts`**, which fails fast at
  boot. Do not scatter `process.env` reads through the codebase.
- **The async handler must keep its top-level `.catch()`.** A rejection escaping into
  `createServer`'s synchronous frame becomes an unhandled rejection and hangs the request.

`GET /health` is the only non-`/trpc` route. It exists so uptime monitors have a cheap
endpoint that does not consume the unknown-path budget and block themselves.

## Frontend (Next.js)

The frontend is a Next.js 16 app with React 19, Tailwind CSS, and Radix UI components.

```bash
cd apps/frontend
npm run dev      # Start dev server
npm run build    # Build for production
npm run lint     # Run ESLint
```

**Tech Stack**:
- Next.js 16 (App Router)
- TypeScript (strict mode)
- Tailwind CSS v4
- Radix UI + shadcn/ui components
- React Hook Form + Zod for forms

### Aggressive Prefetching (Pages & Queries)

Prefetch aggressively so navigation feels instant — regardless of the size of the app (e.g. the number of pages). "Prefetch" always means **both** the frontend (route/components/bundle) **and** warming the underlying data queries — prefetching the UI shell without its data is only half the job. All prefetching must be background, deferred, and non-blocking: it must never delay or compete with rendering the page the user is actually on.

- **Top-level pages**: when the user lands on any top-level page, prefetch all the other top-level pages.
- **Tabs**: when the user lands on a top-level page that has tabs, prefetch all the other tabs of that page.
- **Table rows (hover intent)**: on a page/tab with a table, if the user hovers over a row for more than 200ms, prefetch the result of clicking that row.
- **Paginated tables**: when the user is on one page of a paginated table, prefetch the contents and queries of the next and previous pages.

### Loading Indicators (When Loading Is Unavoidable)

When a user action (clicking a button, etc.) triggers loading, show a small loading dialog only if the loading takes more than 200ms — never instantly. Do **not** accompany the loading dialog with a scrim/backdrop: the scrim causes a flash, and that flash is bad UI.

## Coding Conventions

### Python

**From AGENTS.md**:
- Follow PEP 8 style guidelines
- Use type hints (watch for complex types like `List[Dict[str, Any]]`)
- Add docstrings with parameter descriptions, return values, exceptions
- Include links to documentation/references in comments
- Prefer small, readable functions over complex patterns
- Use pytest for testing

### Key Python Patterns in This Codebase

**1. Database Operations** (see `shared/database.py`):
- Always use context managers for connections
- Batch inserts with `execute_batch()` for performance
- Handle errors with custom exceptions (DatabaseConnectionError, DatabaseOperationError)

**2. Module Imports**:
- Use relative imports within the package: `from shared.database import Database`
- Don't use absolute paths like `from apps.data_ingestion.shared...`

**3. Path Resolution** (see `shared/config.py`):
- Use `get_monorepo_root()` to find repository root (looks for .git directory)
- Use `get_backup_dir(subdir)` to resolve backup paths (handles monorepo structure)
- Never hardcode absolute paths

**4. Logging** (see `shared/config.py`):
- Use `setup_logger()` or `get_logger(__name__)` for consistent logging
- Log to both console and file (`logs/` directory)
- Use appropriate levels (DEBUG, INFO, WARNING, ERROR)

## Important Implementation Details

### Reddit API Rate Limiting

The ingestion scripts include built-in rate limiting:
- 3 seconds between subreddits
- 0.5 seconds between fetching comments for each post
- 10 seconds after API errors
- PRAW handles OAuth token refresh automatically

### Supabase Connection Pooling

The Database class creates a new connection per operation (no pooling yet). For production, consider connection pooling with psycopg2.pool.

### AI Extraction Costs

Claude Sonnet 4 pricing (as of 2025):
- Input: $3 per million tokens
- Output: $15 per million tokens

Typical extraction:
- Post with 5 comments: ~2,000 input tokens, ~300 output tokens
- Cost: ~$0.01 per post

Budget accordingly for large-scale extraction (e.g., 10,000 posts = ~$100).

### Backup File Sizes

Historical ingestion creates large backup files:
- 100 posts + 2000 comments: ~50-100MB JSON file
- Extraction backups: ~5-10MB per subreddit

Ensure sufficient disk space before running batch operations.

## Common Workflows

### Full Pipeline for a New Subreddit

```bash
cd /Users/bryan/Github/which-glp
source venv/bin/activate

# 1. Ingest historical data
python3 -m reddit_ingestion.historical_ingest --subreddit NewSubreddit --posts 100 --comments 20

# 2. Run AI extraction (posts only for speed)
python3 -m extraction.ai_extraction --subreddit NewSubreddit --posts-only

# 3. Verify data in database
psql -h <supabase-url> -U postgres -d postgres -c "SELECT COUNT(*) FROM reddit_posts WHERE subreddit = 'NewSubreddit';"
psql -h <supabase-url> -U postgres -d postgres -c "SELECT COUNT(*) FROM extracted_features WHERE subreddit = 'NewSubreddit';"
```

### Recovery from Failed Ingestion

If ingestion fails mid-process, backups are still created. Upload from backup:

```bash
cd /Users/bryan/Github/which-glp
python3 -m reddit_ingestion.upload_from_backup scripts/legacy-ingestion/ingestion/backup/historical_run_20251003_123456_Ozempic
```

### Adding New Extracted Features

1. Create migration file: `apps/shared/migrations/006_add_new_field.up.sql`
2. Run migration: `python3 apps/shared/migrations/run_migration.py apps/shared/migrations/006_add_new_field.up.sql`
3. Update `extraction/schema.py` to include new field
4. Update `extraction/prompts.py` to instruct Claude to extract new field
5. Re-run extraction for updated posts

## Troubleshooting

### "Module not found" errors

Ensure you've installed the package as editable:
```bash
cd /Users/bryan/Github/which-glp
pip3 install -e scripts/legacy-ingestion
```

### Database connection errors

Verify `.env` file exists in repository root and contains correct credentials. Test connection:
```bash
python3 -c "from shared.database import Database; db = Database(); print('Connected!')"
```

### Reddit API rate limit errors

If you hit rate limits, increase delays in `ingestion/historical_ingest.py`:
```python
DELAY_BETWEEN_SUBREDDITS = 5  # Increase from 3
DELAY_BETWEEN_POSTS = 1.0     # Increase from 0.5
```

### AI extraction timeout errors

Claude API can timeout on large posts. The code already has retry logic with exponential backoff. If it persists, reduce context size in `extraction/context.py`.

## Additional Resources

- **AGENTS.md**: Comprehensive business context, drug information, monetization strategy
- **Supabase Dashboard**: https://app.supabase.com (view tables, run SQL queries)
- **Reddit API Docs**: https://www.reddit.com/dev/api/
- **PRAW Docs**: https://praw.readthedocs.io/
- **Anthropic API Docs**: https://docs.anthropic.com/
