# Benchmarking Scripts

This directory contains performance benchmarking scripts for WhichGLP database queries.

## Overview

These scripts measure query performance to compare the effectiveness of materialized views versus direct table queries. Each script uses PostgreSQL's `EXPLAIN ANALYZE` to show detailed execution plans and timing.

## Understanding getAllStats vs getStats

WhichGLP has two main statistics endpoints with very different purposes and performance characteristics:

### getAllStats (Per-Drug Statistics)

**Location:** `apps/api/src/routers/drugs.ts`
**SQL Function:** `get_drug_stats()`
**Returns:** Array of statistics objects, one per drug

**Purpose:** Provides comprehensive statistics for each GLP-1 drug (Ozempic, Wegovy, Mounjaro, etc.) used on the `/compare` page.

**Data Returned (per drug):**
- Total experience count
- Average weight loss (lbs and percentage)
- Average duration (weeks)
- Average cost per month
- Average sentiment (pre/post treatment)
- Average recommendation score
- Plateau rate (% experiencing weight plateau)
- Rebound rate (% experiencing weight regain)
- Insurance coverage rate
- Drug sources (brand vs compounded counts)
- Side effects (top 10 with counts and severity distribution)
- Side effect reporting rate

**Complexity:** 14+ aggregations per drug with multiple subqueries for side effects

**Example Output:**
```typescript
[
  {
    drug: "Ozempic",
    count: 1523,
    avgWeightLoss: 12.4,
    avgCostPerMonth: 950,
    commonSideEffects: [{ name: "Nausea", count: 456, percentage: 29.9 }, ...],
    ...
  },
  {
    drug: "Wegovy",
    count: 987,
    ...
  },
  ...
]
```

### getStats (Platform-Wide Statistics)

**Location:** `apps/api/src/routers/platform.ts`
**SQL Function:** `get_platform_stats()`
**Returns:** Single statistics object for the entire platform

**Purpose:** Provides high-level platform metrics displayed on the homepage/dashboard.

**Data Returned:**
- Total experiences count
- Unique drugs count
- Locations tracked count
- Average weight loss percentage (placeholder, not yet implemented)

**Complexity:** 3 simple COUNT/DISTINCT aggregations

**Example Output:**
```typescript
{
  totalExperiences: 4109,
  uniqueDrugs: 5,
  locationsTracked: 42,
  avgWeightLossPercentage: 0  // Not implemented yet
}
```

### Key Differences

| Aspect | getAllStats | getStats |
|--------|-------------|----------|
| **Scope** | Per-drug breakdown | Platform-wide totals |
| **Output** | Array of objects | Single object |
| **Aggregations** | 14+ complex aggregations | 3 simple counts |
| **Use Case** | Drug comparison page | Dashboard stats |
| **Performance** | Needs MV (80x speedup) | Simple enough without MV |
| **Cache TTL** | 3 days | Not cached yet |

### experiences.list and experiences.getById

**Location:** `apps/api/src/routers/experiences.ts`

**Purpose:** Lists user experiences with filtering, sorting, and pagination, plus individual experience details.

**experiences.list:**
- Filters by drug, search terms
- Sorts by date, rating, weight loss, etc.
- Paginated (default: 20 per page)
- Used on `/experiences` listing page
- **Performance:** 162ms with MV vs 718ms without (4.4x speedup)

**experiences.getById:**
- Fetches single experience by UUID
- Used on `/experiences/[id]` detail page
- **Performance:** 0.1ms with MV vs 2.6ms without (26x speedup)

## Scripts

### 1. Materialized View Creation
**File:** `benchmark_mv_creation.py`

Benchmarks the creation of the materialized view by running the full DISTINCT ON query with all CASE expressions.

- **Expected Time:** ~3.1 seconds (based on 4,110 rows)
- **Purpose:** Shows how long it takes to build the materialized view from scratch
- **Use Case:** Understanding the cost of refreshing the MV

### 2. getAllStats with MV
**File:** `benchmark_get_all_stats_with_mv.py`

Benchmarks the `getAllStats` query using the `get_drug_stats()` function, which queries the pre-computed materialized view.

- **Query:** `SELECT * FROM get_drug_stats();`
- **Expected Time:** Very fast (milliseconds)
- **Purpose:** Production performance baseline for drug statistics
- **Use Case:** Validating that the MV optimization is working

### 3. getAllStats without MV
**File:** `benchmark_get_all_stats_without_mv.py`

Benchmarks the `getAllStats` query by reconstructing the full aggregation query on base tables (extracted_features, reddit_posts, reddit_comments).

- **Query:** Full CTE with DISTINCT ON + GROUP BY aggregations
- **Expected Time:** Very slow (seconds, similar to MV creation)
- **Purpose:** Show the performance penalty without materialized views
- **Use Case:** Justifying the MV approach

### 4. getStats with MV
**File:** `benchmark_get_stats_with_mv.py`

Benchmarks the `getStats` query using the `get_platform_stats()` function, which queries the materialized view.

- **Query:** `SELECT * FROM get_platform_stats();`
- **Expected Time:** Very fast (milliseconds)
- **Purpose:** Production performance for platform statistics
- **Use Case:** Validating dashboard performance

### 5. getStats without MV
**File:** `benchmark_get_stats_without_mv.py`

Benchmarks the `getStats` query by running aggregations directly on base tables.

- **Query:** Full CTE with DISTINCT ON + COUNT/DISTINCT aggregations
- **Expected Time:** Slow (seconds, similar to MV creation)
- **Purpose:** Show the performance penalty without materialized views
- **Use Case:** Justifying the MV approach for platform stats

### 6. List Experiences with MV
**File:** `benchmark_list_experiences_with_mv.py`

Benchmarks the `experiences.list` query using the materialized view with filters (drug filter), sorting (by date), and pagination (limit 20).

- **Query:** `SELECT * FROM mv_experiences_denormalized WHERE primary_drug = 'Ozempic' ORDER BY created_at DESC LIMIT 20`
- **Expected Time:** Fast (milliseconds)
- **Purpose:** Production performance for experiences listing page
- **Use Case:** Validating listing performance

### 7. List Experiences without MV
**File:** `benchmark_list_experiences_without_mv.py`

Benchmarks the `experiences.list` query by running deduplication, joins, and pagination on base tables.

- **Query:** Full CTE with DISTINCT ON + filters + sorting + pagination
- **Expected Time:** Slow (hundreds of milliseconds)
- **Purpose:** Show the performance penalty without materialized views
- **Use Case:** Justifying the MV approach for experiences listing

### 8. Get Experience by ID with MV
**File:** `benchmark_get_experience_by_id_with_mv.py`

Benchmarks the `experiences.getById` query using the materialized view.

- **Query:** `SELECT * FROM mv_experiences_denormalized WHERE feature_id = [uuid]`
- **Expected Time:** Very fast (sub-millisecond)
- **Purpose:** Production performance for single experience detail page
- **Use Case:** Validating detail page performance

### 9. Get Experience by ID without MV
**File:** `benchmark_get_experience_by_id_without_mv.py`

Benchmarks the `experiences.getById` query by joining base tables.

- **Query:** Direct join with extracted_features, reddit_posts, reddit_comments by ID
- **Expected Time:** Fast (a few milliseconds)
- **Purpose:** Show performance of direct table queries for single-row lookups
- **Use Case:** Understanding index scan performance

## Running Benchmarks

### Prerequisites

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Ensure `.env` file contains:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_DB_PASSWORD=your-password
   ```

### Run Individual Benchmarks

From the repository root:

```bash
# Benchmark MV creation time
python3 scripts/benchmarking/benchmark_mv_creation.py

# Benchmark getAllStats (with MV - FAST)
python3 scripts/benchmarking/benchmark_get_all_stats_with_mv.py

# Benchmark getAllStats (without MV - SLOW)
python3 scripts/benchmarking/benchmark_get_all_stats_without_mv.py

# Benchmark getStats (with MV - FAST)
python3 scripts/benchmarking/benchmark_get_stats_with_mv.py

# Benchmark getStats (without MV - SLOW)
python3 scripts/benchmarking/benchmark_get_stats_without_mv.py

# Benchmark list experiences (with MV - FAST)
python3 scripts/benchmarking/benchmark_list_experiences_with_mv.py

# Benchmark list experiences (without MV - SLOW)
python3 scripts/benchmarking/benchmark_list_experiences_without_mv.py

# Benchmark get experience by ID (with MV - VERY FAST)
python3 scripts/benchmarking/benchmark_get_experience_by_id_with_mv.py

# Benchmark get experience by ID (without MV - FAST)
python3 scripts/benchmarking/benchmark_get_experience_by_id_without_mv.py
```

### Run All Benchmarks

```bash
for script in scripts/benchmarking/benchmark_*.py; do
  echo "Running $script..."
  python3 "$script"
  echo ""
done
```

## Understanding Results

### Key Metrics to Look For

1. **Execution Time:** How long the query took (shown at bottom of EXPLAIN ANALYZE)
2. **Planning Time:** PostgreSQL query planning overhead
3. **Seq Scan vs Index Scan:** Index scans are faster
4. **Sort Method:** In-memory sorts are faster than disk-based
5. **Rows Processed:** How many rows were scanned

### Expected Performance Gains

**With Materialized View:**
- getAllStats: ~14ms (instant)
- getStats: ~88ms (fast, but CTE overhead)
- List experiences: ~162ms (fast)
- Get experience by ID: ~0.1ms (extremely fast)

**Without Materialized View:**
- getAllStats: ~1,129ms (1.1 seconds - slow)
- getStats: ~24ms (faster than MV due to simplicity)
- List experiences: ~718ms (slow)
- Get experience by ID: ~2.6ms (fast)

**Performance Improvement:**
- getAllStats: 80x faster with MV
- List experiences: 4.4x faster with MV
- Get by ID: 26x faster with MV

## Technical Details

### What the Scripts Do

Each script follows this workflow:

1. **Connect** to Supabase PostgreSQL database
2. **Enable** EXPLAIN for PostgREST (`pgrst.db_plan_enabled = 'true'`)
3. **Reload** PostgREST config to apply changes
4. **Run** `EXPLAIN ANALYZE` on the target query
5. **Print** detailed query plan and timing
6. **Disable** EXPLAIN for PostgREST
7. **Reload** PostgREST config again
8. **Close** database connection

### Why Enable/Disable EXPLAIN?

PostgREST's `pgrst.db_plan_enabled` setting controls whether query plans are exposed via the API. We enable it temporarily for benchmarking, then disable it for security.

### Query Differences

**With MV:**
- Queries use simple `SELECT * FROM function_name()`
- Functions internally query `mv_experiences_denormalized`
- All complex CASE expressions are pre-computed

**Without MV:**
- Queries reconstruct the entire materialized view logic
- DISTINCT ON deduplication happens at query time
- 60+ CASE expressions evaluated for every row
- Multiple table joins (extracted_features, reddit_posts, reddit_comments)

## Notes

- All benchmarks are read-only and safe to run in production
- Results may vary based on database size and server load
- Scripts automatically clean up (disable EXPLAIN) even on error
- Connection details are pulled from `.env` file (git-ignored)

## See Also

- `/apps/shared/migrations/020_filter_mv_empty_summaries.up.sql` - MV creation query
- `/apps/shared/migrations/018_create_stats_aggregation_functions.up.sql` - SQL functions
- `/apps/api/src/routers/drugs.ts` - getAllStats implementation
- `/apps/api/src/routers/platform.ts` - getStats implementation
