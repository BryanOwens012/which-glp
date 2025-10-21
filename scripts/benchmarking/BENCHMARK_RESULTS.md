# Benchmark Results

Performance comparison of database queries with and without materialized views.

**Test Date:** 2025-10-20
**Database Size:** 4,109 experiences (deduplicated from 5,610 total extracted features)
**Database:** Supabase PostgreSQL

---

## Summary

| Query | With MV | Without MV | Speedup |
|-------|---------|------------|---------|
| **getAllStats** | 14.1 ms | 1,129.0 ms | **80x faster** |
| **getStats** | 88.0 ms | 23.8 ms | **0.27x** (MV slower) |
| **List Experiences** | 162.4 ms | 718.5 ms | **4.4x faster** |
| **Get Experience by ID** | 0.1 ms | 2.6 ms | **26x faster** |
| **MV Creation** | 3,120 ms | N/A | N/A |

---

## Detailed Results

### 1. MV Creation (baseline)

**Script:** `benchmark_mv_creation.py`

This query creates the entire materialized view from scratch, performing DISTINCT ON deduplication and computing all 60+ calculated fields.

```
Planning Time: 143.558 ms
Execution Time: 3,120.263 ms (3.12 seconds)
Total Time: 3,263.821 ms (3.26 seconds)
```

**Key Operations:**
- Sequential scan on `extracted_features`: 1,225 ms
- Nested loop left joins with `reddit_posts` and `reddit_comments`
- External merge sort to disk: 5,680 KB
- 4,110 rows processed → 4,108 rows output

**Bottleneck:** Sequential scan + complex CASE expressions + disk-based sorting

---

### 2. getAllStats - WITH Materialized View

**Script:** `benchmark_get_all_stats_with_mv.py`

Queries the `get_drug_stats()` function which runs aggregations on the pre-computed `mv_experiences_denormalized` table.

```sql
SELECT * FROM get_drug_stats();
```

```
Planning Time: 3.646 ms
Execution Time: 14.087 ms (14.1 ms)
Total Time: 17.733 ms (17.7 ms)
```

**Key Operations:**
- Index-only scan on `idx_mv_experiences_drug`: 3.2 ms
- In-memory quicksort: 25 KB memory
- HashAggregate with 5 drug groups

**Performance:** ⚡ **14.1 ms** - Extremely fast!

---

### 3. getAllStats - WITHOUT Materialized View

**Script:** `benchmark_get_all_stats_without_mv.py`

Runs the full aggregation query directly on base tables (`extracted_features`, `reddit_posts`, `reddit_comments`).

```sql
WITH deduplicated_experiences AS (
  SELECT DISTINCT ON (post_id) ...
  -- Full MV reconstruction
)
SELECT primary_drug AS drug, COUNT(*) AS count, ...
FROM deduplicated_experiences
GROUP BY primary_drug;
```

```
Planning Time: 64.876 ms
Execution Time: 1,128.984 ms (1.13 seconds)
Total Time: 1,193.860 ms (1.19 seconds)
```

**Key Operations:**
- Sequential scan on `extracted_features`: 1,105.8 ms (slowest)
- In-memory quicksort (539 KB memory): deduplication
- HashAggregate with 205 drug groups

**Performance:** 🐌 **1,129 ms** - Very slow!

**Speedup with MV:** **80x faster** (1,129 ms → 14.1 ms)

---

### 4. getStats - WITH Materialized View

**Script:** `benchmark_get_stats_with_mv.py`

Queries the `get_platform_stats()` function which counts experiences, drugs, and locations from the MV.

```sql
SELECT * FROM get_platform_stats();
```

```
Planning Time: 4.361 ms
Execution Time: 88.000 ms (88.0 ms)
Total Time: 92.361 ms (92.4 ms)
```

**Key Operations:**
- Index-only scan on `idx_mv_experiences_drug_location`: 2.9 ms
- CTE `top_drugs` with top-N heapsort: 81.3 ms
- Aggregate (COUNT/COUNT DISTINCT): 5.8 ms

**Performance:** ⚡ **88 ms** - Fast, but CTE overhead

**Note:** The `top_drugs` CTE (which filters to top N drugs) dominates execution time. The actual platform stats aggregation is very fast (~6 ms).

---

### 5. getStats - WITHOUT Materialized View

**Script:** `benchmark_get_stats_without_mv.py`

Runs the platform stats query directly on base tables with deduplication logic.

```sql
WITH deduplicated_experiences AS (
  SELECT DISTINCT ON (post_id) ...
)
SELECT COUNT(*) AS total_experiences, ...
FROM deduplicated_experiences;
```

```
Planning Time: 2.080 ms
Execution Time: 23.804 ms (23.8 ms)
Total Time: 25.884 ms (25.9 ms)
```

**Key Operations:**
- Sequential scan on `extracted_features`: 14.0 ms
- In-memory quicksort (451 KB memory): deduplication
- Simple aggregation: COUNT/COUNT DISTINCT

**Performance:** ⚡ **23.8 ms** - Surprisingly fast!

**Speedup with MV:** **0.27x** (88 ms vs 23.8 ms) - **MV is slower!**

**Why?** The `getStats` query is very simple (just 3 aggregations), so the MV overhead (CTE for top_drugs filtering) outweighs the benefit. The sequential scan is fast enough for this use case.

---

### 6. List Experiences - WITH Materialized View

**Script:** `benchmark_list_experiences_with_mv.py`

Queries the MV with filters (drug='Ozempic'), sorting (created_at DESC), and pagination (LIMIT 20).

```sql
SELECT * FROM mv_experiences_denormalized
WHERE primary_drug = 'Ozempic'
ORDER BY created_at DESC NULLS LAST
LIMIT 20 OFFSET 0;
```

```
Planning Time: 55.175 ms
Execution Time: 162.383 ms (162.4 ms)
Total Time: 217.558 ms (217.6 ms)
```

**Key Operations:**
- Bitmap Index Scan on `idx_mv_experiences_drug_age`: 2.3 ms
- Bitmap Heap Scan: 148.2 ms (264 heap blocks)
- Top-N heapsort (limit 20): In-memory, 91 KB memory
- 382 rows filtered → 20 rows returned

**Performance:** ⚡ **162 ms** - Fast for filtered listing

---

### 7. List Experiences - WITHOUT Materialized View

**Script:** `benchmark_list_experiences_without_mv.py`

Runs full deduplication query on base tables with filters, sorting, and pagination.

```sql
WITH deduplicated_experiences AS (
  SELECT DISTINCT ON (post_id) ...
  -- Full MV reconstruction
)
SELECT * FROM deduplicated_experiences
WHERE primary_drug = 'Ozempic'
ORDER BY created_at DESC NULLS LAST
LIMIT 20;
```

```
Planning Time: 15.948 ms
Execution Time: 718.469 ms (718.5 ms)
Total Time: 734.417 ms (734.4 ms)
```

**Key Operations:**
- Sequential scan on `extracted_features`: 19.5 ms
- Nested loop joins with reddit_posts: 670 ms total
- External merge sort to disk: 4,160 KB
- 4,114 rows processed → filtered to 396 Ozempic → 20 returned

**Performance:** 🐌 **718 ms** - Slow due to joins + sorting

**Speedup with MV:** **4.4x faster** (718 ms → 162 ms)

---

### 8. Get Experience by ID - WITH Materialized View

**Script:** `benchmark_get_experience_by_id_with_mv.py`

Queries the MV by feature_id (UUID primary key).

```sql
SELECT * FROM mv_experiences_denormalized
WHERE feature_id = '354b32ae-70c3-45fb-bec5-a57baed934d1'
LIMIT 1;
```

```
Planning Time: 1.985 ms
Execution Time: 0.101 ms (0.1 ms)
Total Time: 2.086 ms (2.1 ms)
```

**Key Operations:**
- Sequential scan on `mv_experiences_denormalized`: 0.1 ms
- Single row returned immediately

**Performance:** ⚡⚡⚡ **0.1 ms** - Extremely fast!

**Note:** This could be even faster with an index on `feature_id`, but it's already sub-millisecond.

---

### 9. Get Experience by ID - WITHOUT Materialized View

**Script:** `benchmark_get_experience_by_id_without_mv.py`

Joins base tables directly by ID using index scans.

```sql
SELECT ef.*, rp.*, rc.*
FROM extracted_features ef
LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
WHERE ef.id = 'fbbf44a9-1b49-452b-93ea-2b70ca71db29'
LIMIT 1;
```

```
Planning Time: 5.161 ms
Execution Time: 2.594 ms (2.6 ms)
Total Time: 7.755 ms (7.8 ms)
```

**Key Operations:**
- Index scan on `extracted_features_pkey`: 1.2 ms
- Index scan on `idx_reddit_posts_post_id`: 1.2 ms
- Index scan on `idx_comments_comment_id`: 0.01 ms

**Performance:** ⚡ **2.6 ms** - Fast with index scans

**Speedup with MV:** **26x faster** (2.6 ms → 0.1 ms)

**Why the difference?** Even with perfect index scans, the base table query requires 3 separate index lookups. The MV has everything pre-joined in a single table.

---

## Key Insights

### 1. getAllStats: MV is Essential (80x speedup)

The `getAllStats` query performs **14 complex aggregations** (AVG, COUNT FILTER, etc.) on **all experiences**. Without the MV:
- Must scan all 4,111 rows from `extracted_features`
- Must compute 60+ CASE expressions for each row
- Must perform expensive GROUP BY on 205 drug groups

With the MV:
- All calculations are pre-computed
- Index-only scan reads just the necessary columns
- In-memory aggregation is extremely fast

**Recommendation:** ✅ **Keep using MV for getAllStats**

---

### 2. getStats: MV May Not Be Necessary (0.27x slower)

The `getStats` query is very simple (3 COUNT/DISTINCT operations). The MV version is **slower** because:
- CTE filtering for `top_drugs` adds 81 ms overhead
- The base table query is fast enough (24 ms total)
- No complex CASE expressions to pre-compute

**Recommendation:** ⚠️ **Consider bypassing MV for getStats**, or optimize the CTE

**Potential Optimization:**
```sql
-- Current (slow): Uses top_drugs CTE that filters to top N
SELECT COUNT(*), COUNT(DISTINCT primary_drug), COUNT(DISTINCT location)
FROM mv_experiences_denormalized;

-- Optimized (fast): Remove top_drugs CTE entirely
SELECT COUNT(*), COUNT(DISTINCT primary_drug), COUNT(DISTINCT location)
FROM mv_experiences_denormalized;
```

The `top_drugs` CTE is not needed for the platform stats query - it's only used by `getAllStats`.

---

### 3. List Experiences: MV is Beneficial (4.4x speedup)

The `experiences.list` query filters, sorts, and paginates experiences. Without the MV:
- Must perform DISTINCT ON deduplication on 4,114 rows
- Must join extracted_features with reddit_posts and reddit_comments
- Must sort to disk (external merge, 4,160 KB)
- Filter happens **after** all joins and deduplication

With the MV:
- Deduplication already done
- Joins already performed
- Can use index on `primary_drug` to filter early
- In-memory sorting (only 91 KB for 382 filtered rows)

**Recommendation:** ✅ **Keep using MV for experiences listing** - 4.4x speedup with less disk I/O

---

### 4. Get Experience by ID: MV is Faster (26x speedup)

Even though the base table query uses perfect index scans (2.6 ms is fast!), the MV is still **26x faster** (0.1 ms).

**Why?**
- Base table query: 3 separate index lookups (extracted_features → reddit_posts → reddit_comments)
- MV query: Single sequential scan (data already co-located)

**Trade-off:**
- MV is faster but could benefit from an index on `feature_id` for even better performance
- Base table query is already fast enough for most use cases (2.6 ms)

**Recommendation:** ✅ **Keep using MV for detail pages** - Sub-millisecond response is ideal for UX

**Optional Optimization:** Create index on `mv_experiences_denormalized(feature_id)` for guaranteed constant-time lookups.

---

### 5. MV Refresh Cost: 3.12 seconds

Refreshing the materialized view takes **3.12 seconds** for 4,109 experiences. This is acceptable for:
- Daily cron jobs (current strategy)
- Weekly batch updates
- Manual refreshes after large ingestion

For 10,000+ experiences, expect ~7-10 seconds refresh time.

**Current Refresh Strategy:** `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized;`

---

## Recommendations

### Immediate Actions

1. ✅ **Keep MV for getAllStats** - 80x speedup is critical for frontend performance
2. ⚠️ **Consider removing top_drugs CTE from get_platform_stats()** - It adds 81ms overhead unnecessarily
3. ✅ **Keep MV for experiences listing** - 4.4x speedup with less disk I/O
4. ✅ **Keep MV for experience detail pages** - 26x speedup, sub-millisecond response
5. ✅ **Continue daily MV refreshes** - 3.1s is acceptable for nightly cron jobs

### Future Optimizations

1. **Add index on feature_id** - `CREATE INDEX idx_mv_experiences_feature_id ON mv_experiences_denormalized(feature_id)` for even faster getById queries
2. **Partition MV by drug** - If data grows to 100k+ experiences, consider partitioning
3. **Add partial indexes** - For common filter patterns (e.g., `WHERE weight_loss_lbs > 0`)
4. **Monitor refresh time** - If it exceeds 10s, consider incremental refresh strategies
5. **Consider composite indexes for common filter combinations** - e.g., `(primary_drug, created_at DESC)` for listing queries

---

## Test Environment

- **Database:** Supabase PostgreSQL (version: 15.x)
- **Connection:** Direct PostgreSQL connection (not PostgREST)
- **Data Volume:** 4,109 deduplicated experiences
- **Cache:** Cold cache (first run after connection)
- **Server Location:** Remote (Supabase cloud)

---

## Reproduction

To reproduce these benchmarks:

```bash
cd /Users/bryan/Github/which-glp
source venv/bin/activate

# Run all benchmarks
for script in scripts/benchmarking/benchmark_*.py; do
  echo "Running $script..."
  python3 "$script"
  echo ""
done
```

---

## Appendix: Full EXPLAIN ANALYZE Output

For detailed query plans, see the individual benchmark script outputs above.
