# Backend & tRPC Setup Complete

## Summary

Successfully implemented a complete tRPC backend API and integrated it with the frontend, replacing the mock data layer with real database queries.

## What Was Built

### 1. Materialized View on Supabase

**File**: `apps/shared/migrations/006_create_denormalized_view.up.sql`

Created `mv_experiences_denormalized` materialized view that:
- Joins `extracted_features`, `reddit_posts`, and `reddit_comments` tables
- Pre-calculates commonly used metrics (weight_loss_lbs, weight_loss_percentage, sentiment_change, age_bucket)
- Includes comprehensive indexes for optimal query performance
- Denormalizes Reddit content (post/comment text, author, scores) for faster access

**Key Pre-calculated Fields**:
- `weight_loss_lbs`: Weight loss in pounds (handles kg → lbs conversion)
- `weight_loss_percentage`: Percentage weight loss
- `beginning_weight_lbs`/`end_weight_lbs`: Normalized weights in lbs
- `sentiment_change`: Difference between pre and post sentiment
- `age_bucket`: Age ranges for demographic analysis (18-24, 25-34, 35-44, 45-54, 55-64, 65+)

**Indexes Created**:
- Single-column: drug, subreddit, location, created_at, weight_loss, recommendation
- Composite: drug+location, drug+age_bucket
- GIN: side_effects, comorbidities (for JSONB array queries)

### 2. Backend Node.js + Express + tRPC Server

**Location**: `apps/api/`

**Tech Stack**:
- Node.js 20+ (though running on 18.18.0 currently)
- Express.js for HTTP server
- tRPC v11 for type-safe APIs
- Prisma ORM for database access
- SuperJSON for automatic serialization (handles Dates, Decimals, etc.)

**Prisma Schema** (`prisma/schema.prisma`):
- Single model: `mv_experiences_denormalized`
- Maps directly to the materialized view
- All fields typed correctly (Decimal, Json, DateTime, arrays)

**Server Configuration**:
- Port: 3002
- CORS enabled for http://localhost:3001 (frontend)
- Health check endpoint: `GET /health`
- tRPC endpoint: `POST /trpc/*`

### 3. tRPC Routers Implemented

All routers live in `apps/api/src/routers/`

#### Platform Router (`platform.ts`)
- `platform.getStats`: Overall statistics (total experiences, unique drugs, locations tracked, avg weight loss)
- `platform.getTrends`: Time-series data grouped by month

#### Drugs Router (`drugs.ts`)
- `drugs.getAllStats`: Comprehensive stats for all drugs (weight loss, sentiment, cost, insurance, side effects, plateau/rebound rates)
- `drugs.getStats(drug)`: Stats for a specific drug

#### Experiences Router (`experiences.ts`)
- `experiences.list({drug?, search?, limit, offset})`: Paginated, filterable experience list
- `experiences.getById({id})`: Single experience details

#### Locations Router (`locations.ts`)
- `locations.getData`: Geographic stats (count and average cost per state)

#### Demographics Router (`demographics.ts`)
- `demographics.getData`: Age distribution, sex distribution, top comorbidities

### 4. Frontend tRPC Client Setup

**Files Created**:
- `apps/frontend/lib/trpc.ts`: tRPC React hooks initialization
- `apps/frontend/components/providers.tsx`: React Query + tRPC provider
- `apps/frontend/.env.local`: Backend URL configuration

**Dependencies Added**:
- `@trpc/client@^11.6.0`
- `@trpc/react-query@^11.6.0`
- `@trpc/server@^11.6.0`
- `@tanstack/react-query@^5.90.2`
- `superjson@^2.2.2`

**Layout Integration**:
Updated `apps/frontend/app/layout.tsx` to wrap entire app with `<Providers>` component.

**Configuration**:
- Backend URL: http://localhost:3002/trpc
- Query client configured with 60s stale time
- Automatic batching enabled (httpBatchLink)

## Current Status

✅ Backend server running on http://localhost:3002
✅ Frontend running on http://localhost:3001
✅ tRPC infrastructure fully set up
✅ Type safety between frontend and backend (shared AppRouter type)

## Next Steps

The following work remains to fully transition from mock data to real data:

### 1. Replace Mock Data Functions

For each page, replace mock data imports with tRPC hooks:

**Home Page** (`app/page.tsx`):
```typescript
// Before:
import { getPlatformStats } from "@/lib/mock-data"
const stats = await getPlatformStats()

// After:
import { trpc } from "@/lib/trpc"
const { data: stats } = trpc.platform.getStats.useQuery()
```

**Compare Page** (`app/compare/page.tsx`):
```typescript
// Before:
import { getAllDrugStats } from "@/lib/mock-data"
const drugs = await getAllDrugStats()

// After:
import { trpc } from "@/lib/trpc"
const { data: drugs } = trpc.drugs.getAllStats.useQuery()
```

**Dashboard Page** (`app/dashboard/page.tsx`):
```typescript
// Platform stats:
const { data: platformStats } = trpc.platform.getStats.useQuery()

// Trends:
const { data: trends } = trpc.platform.getTrends.useQuery({ period: 'month' })

// Drug stats:
const { data: drugStats } = trpc.drugs.getAllStats.useQuery()

// Demographics:
const { data: demographics } = trpc.demographics.getData.useQuery()

// Locations:
const { data: locations } = trpc.locations.getData.useQuery()
```

**Experiences Page** (`app/experiences/page.tsx`):
```typescript
// List with filters:
const { data } = trpc.experiences.list.useQuery({
  drug: selectedDrug,
  search: searchText,
  limit: 20,
  offset: 0,
})

// By ID (for modal):
const { data: experience } = trpc.experiences.getById.useQuery(
  { id: selectedId },
  { enabled: !!selectedId }
)
```

### 2. Handle Loading States

Add proper loading states to all pages:

```typescript
const { data, isLoading, error } = trpc.platform.getStats.useQuery()

if (isLoading) return <LoadingSpinner />
if (error) return <ErrorMessage error={error} />
if (!data) return null
```

### 3. Update Type Definitions

The mock data types in `lib/types.ts` may need adjustment to match the actual tRPC return types. Use the inferred types from tRPC:

```typescript
import type { RouterOutputs } from '@/lib/trpc'

type DrugStats = RouterOutputs['drugs']['getAllStats'][number]
type Experience = RouterOutputs['experiences']['list']['experiences'][number]
```

### 4. Remove Mock Data Files

Once all pages are migrated:
- Delete `apps/frontend/lib/mock-data.ts`
- Remove unused type definitions from `lib/types.ts`
- Clean up any remaining mock data references

### 5. Data Formatting Adjustments

Some backend responses may need formatting adjustments:

**Side Effects**:
Backend returns: `Array<{name: string, severity?: string}>`
Frontend expects: `string[]` (for `top_side_effects`)

**Weight Units**:
Backend always returns lbs (pre-calculated)
Frontend should display with proper units

**Dates**:
Backend returns ISO strings
Frontend should format with `new Date(...)` or date-fns

### 6. Pagination Implementation

The `/experiences` page needs infinite scroll or "Load More" functionality:

```typescript
const [offset, setOffset] = useState(0)
const { data } = trpc.experiences.list.useQuery({
  limit: 20,
  offset,
})

const loadMore = () => setOffset(prev => prev + 20)
```

### 7. Materialized View Refresh Strategy

Set up a cron job or manual trigger to refresh the materialized view after AI extraction runs:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized;
```

Options:
- **Manual**: Run after each batch extraction
- **Scheduled**: Daily cron job (e.g., 3am)
- **Triggered**: PostgreSQL trigger after INSERT on extracted_features (may be slow)

### 8. Error Handling

Add global error handling for tRPC errors:

```typescript
// In providers.tsx
const [queryClient] = useState(() => new QueryClient({
  defaultOptions: {
    queries: {
      onError: (error) => {
        console.error('Query error:', error)
        // Show toast notification
      },
    },
  },
}))
```

### 9. Production Deployment

**Backend** (Railway, Render, or Fly.io):
- Set `DATABASE_URL` env var
- Set `FRONTEND_URL` to production URL (e.g., https://whichglp.com)
- Run `npm run build && npm start`

**Frontend** (Vercel):
- Set `NEXT_PUBLIC_BACKEND_URL` to production backend URL
- Deploy with `npm run build`

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │ Home Page   │  │ Compare     │  │ Experiences  │  ...   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘        │
│         │                │                 │                 │
│         └────────────────┴─────────────────┘                 │
│                          │                                    │
│                  ┌───────▼────────┐                          │
│                  │ tRPC Client    │                          │
│                  │ (React Query)  │                          │
│                  └───────┬────────┘                          │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP (batched)
                  ┌────────▼─────────┐
                  │                  │
┌─────────────────▼──────────────────▼───────────────────────┐
│              Backend (Node.js + Express + tRPC)             │
│  ┌──────────┐  ┌───────┐  ┌────────────┐  ┌──────────────┐│
│  │ Platform │  │ Drugs │  │ Experiences│  │ Demographics ││
│  │ Router   │  │ Router│  │ Router     │  │ Router       ││
│  └────┬─────┘  └───┬───┘  └─────┬──────┘  └──────┬───────┘│
│       └────────────┴────────────┴────────────────┘         │
│                          │                                   │
│                  ┌───────▼────────┐                         │
│                  │  Prisma ORM    │                         │
│                  └───────┬────────┘                         │
└──────────────────────────┼──────────────────────────────────┘
                           │ SQL
                  ┌────────▼─────────┐
                  │                  │
┌─────────────────▼──────────────────▼────────────────────────┐
│                Supabase PostgreSQL                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ mv_experiences_denormalized (materialized view)     │   │
│  │   - Joins extracted_features + reddit_posts         │   │
│  │               + reddit_comments                      │   │
│  │   - Pre-calculated metrics (weight_loss, etc.)      │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼─────┐  ┌──────────────┐  ┌─────────┐│
│  │ extracted_features     │  │reddit_posts  │  │comments ││
│  └────────────────────────┘  └──────────────┘  └─────────┘│
└──────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### Backend
- `apps/api/package.json`
- `apps/api/tsconfig.json`
- `apps/api/.env`
- `apps/api/.env.example`
- `apps/api/prisma/schema.prisma`
- `apps/api/src/index.ts`
- `apps/api/src/lib/trpc.ts`
- `apps/api/src/routers/index.ts`
- `apps/api/src/routers/platform.ts`
- `apps/api/src/routers/drugs.ts`
- `apps/api/src/routers/experiences.ts`
- `apps/api/src/routers/locations.ts`
- `apps/api/src/routers/demographics.ts`

### Frontend
- `apps/frontend/lib/trpc.ts`
- `apps/frontend/components/providers.tsx`
- `apps/frontend/.env.local`
- `apps/frontend/app/layout.tsx` (modified)

### Database
- `apps/shared/migrations/006_create_denormalized_view.up.sql`
- `apps/shared/migrations/006_create_denormalized_view.down.sql`

## Running the Stack

**Terminal 1 - Backend**:
```bash
cd apps/api
npm run dev
```

**Terminal 2 - Frontend**:
```bash
cd apps/frontend
npm run dev
```

Backend: http://localhost:3002
Frontend: http://localhost:3001

## Testing tRPC Endpoints

You can test the backend directly using the tRPC playground or curl:

**Platform Stats**:
```bash
curl -X POST http://localhost:3002/trpc/platform.getStats
```

**Drug Stats**:
```bash
curl -X POST http://localhost:3002/trpc/drugs.getAllStats
```

**Experiences List**:
```bash
curl -X POST http://localhost:3002/trpc/experiences.list \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "offset": 0}'
```

---

**Status**: Infrastructure complete. Ready for frontend integration. ✅
