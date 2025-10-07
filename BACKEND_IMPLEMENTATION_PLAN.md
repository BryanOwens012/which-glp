# Backend Implementation Plan - tRPC + Prisma + Materialized Views

## Overview
Implement type-safe backend APIs using tRPC to replace mock data in frontend. Create optimized materialized views in Supabase for complex aggregations.

---

## Frontend Data Requirements Analysis

### 1. Home Page (`/`)
**Data Needed:**
- Platform stats: total experiences, total drugs, avg weight loss, states/countries tracked

**API Endpoint:**
- `platform.getStats()` → `{ totalExperiences, totalDrugs, avgWeightLoss, statesTracked, countriesTracked }`

---

### 2. Compare Page (`/compare`)
**Data Needed:**
- All drug statistics with aggregations:
  - Drug name, count of experiences
  - Average weight loss (%, lbs)
  - Average duration (weeks)
  - Average cost per month
  - Average sentiment (pre, post, recommendation score)
  - Insurance coverage rate
  - Common side effects with frequencies
  - Side effect severity distribution
  - Drug source breakdown (brand, compounded, out-of-pocket, other)
  - Pharmacy access issues rate
  - Plateau rate, rebound rate

**API Endpoints:**
- `drugs.getAllStats()` → `DrugStats[]`
- `drugs.getStats(drugName)` → `DrugStats | null`

**Aggregations Required:**
- Weight loss: Calculate `(beginning_weight - end_weight) / beginning_weight * 100`
- Handle JSONB fields: `beginning_weight`, `end_weight`, `side_effects`
- Group by `primary_drug`
- Count occurrences from arrays

---

### 3. Dashboard Page (`/dashboard`)
**Data Needed:**
- **Drug stats** (same as compare page)
- **Location data:**
  - State/country grouping
  - Average cost per location
  - Experience count per location
  - Pharmacy access issues rate
  - Top drugs per location
- **Demographics:**
  - Age distribution (bucketed: 18-29, 30-39, 40-49, 50-59, 60+)
  - Sex distribution (including unknown/NULL)
  - Top comorbidities with counts
- **Trend data:**
  - Monthly experience volume
  - Average weight loss over time
  - Growth metrics

**API Endpoints:**
- `drugs.getAllStats()` → `DrugStats[]`
- `locations.getData()` → `LocationData[]`
- `demographics.getData()` → `DemographicData`
- `platform.getStats()` → Platform-wide metrics
- `trends.getData()` → Time-series data

**Aggregations Required:**
- Geographic grouping by `state`/`country`
- Age bucketing with CASE statements
- Flatten ARRAY fields (`comorbidities`) and count occurrences
- Time-series grouping by `DATE_TRUNC('month', processed_at)`

---

### 4. Experiences Page (`/experiences`)
**Data Needed:**
- List of experience cards:
  - ID, post_id, comment_id (for Reddit links)
  - Summary
  - Primary drug
  - Calculated weight loss (amount + unit)
  - Duration in weeks
  - Sentiment post, recommendation score
  - Top 3 side effects
  - Cost per month
  - Age, sex, location
  - Processed timestamp
- Filterable by: drug, text search
- Drug list for filter dropdown

**API Endpoints:**
- `experiences.list(filters)` → `{ experiences: ExperienceCard[], total: number }`
  - Filters: `{ drug?, search?, limit?, offset? }`
- `drugs.getAllStats()` → For dropdown options

**Calculations Required:**
- Weight loss: Extract from JSONB `beginning_weight` and `end_weight`
- Top 3 side effects: Parse JSONB `side_effects` array, sort by severity/count
- Full-text search on `summary` field

---

### 5. Predict Page (`/predict`)
**Data Needed:**
- Similarity matching based on user input
- For each drug:
  - Expected weight loss range (min, max, avg) for similar users
  - Success rate (% achieving goal)
  - Side effect probabilities for similar users
  - Cost estimates
  - Similar user count

**API Endpoints:**
- `predictions.generate(input)` → `PredictionResult[]`
  - Input: `{ currentWeight, goalWeight, age, sex, state?, comorbidities[], hasInsurance, maxBudget?, sideEffectConcerns[] }`

**Complex Logic:**
- Find similar users: age ±5 years, same sex, overlapping comorbidities
- Calculate statistics for similar cohort per drug
- Rank drugs by predicted match score
- Adjust cost estimates based on insurance

---

## Database Schema Additions

### Materialized View: `mv_experiences_denormalized`

**Purpose:** Denormalize `extracted_features`, `reddit_posts`, and `reddit_comments` for fast queries

**Schema:**
```sql
CREATE MATERIALIZED VIEW mv_experiences_denormalized AS
SELECT
  -- IDs
  ef.id,
  ef.post_id,
  ef.comment_id,

  -- Reddit metadata (joined from posts/comments)
  COALESCE(rp.subreddit, rc_sub.subreddit) as subreddit,
  COALESCE(rp.author, rc.author) as reddit_author,
  COALESCE(rp.created_utc, rc.created_utc) as reddit_created_utc,
  COALESCE(rp.score, rc.score) as reddit_score,

  -- Extracted features (all columns)
  ef.summary,
  ef.beginning_weight,
  ef.end_weight,
  ef.duration_weeks,
  ef.cost_per_month,
  ef.currency,
  ef.drugs_mentioned,
  ef.primary_drug,
  ef.drug_sentiments,
  ef.sentiment_pre,
  ef.sentiment_post,
  ef.recommendation_score,
  ef.has_insurance,
  ef.insurance_provider,
  ef.side_effects,
  ef.comorbidities,
  ef.location,
  ef.age,
  ef.sex,
  ef.state,
  ef.country,
  ef.dosage_progression,
  ef.exercise_frequency,
  ef.dietary_changes,
  ef.previous_weight_loss_attempts,
  ef.drug_source,
  ef.switching_drugs,
  ef.side_effect_timing,
  ef.side_effect_resolution,
  ef.food_intolerances,
  ef.plateau_mentioned,
  ef.rebound_weight_gain,
  ef.labs_improvement,
  ef.medication_reduction,
  ef.nsv_mentioned,
  ef.support_system,
  ef.pharmacy_access_issues,
  ef.mental_health_impact,
  ef.model_used,
  ef.confidence_score,
  ef.processed_at,

  -- Calculated fields
  -- Weight loss in pounds (handle unit conversion)
  CASE
    WHEN (ef.beginning_weight->>'value') IS NOT NULL
      AND (ef.end_weight->>'value') IS NOT NULL
      AND (ef.beginning_weight->>'unit') IS NOT NULL
      AND (ef.end_weight->>'unit') IS NOT NULL
    THEN
      CASE
        WHEN (ef.beginning_weight->>'unit') = 'kg'
        THEN ((ef.beginning_weight->>'value')::float * 2.20462) -
             (CASE WHEN (ef.end_weight->>'unit') = 'kg'
                   THEN (ef.end_weight->>'value')::float * 2.20462
                   ELSE (ef.end_weight->>'value')::float END)
        ELSE (ef.beginning_weight->>'value')::float -
             (CASE WHEN (ef.end_weight->>'unit') = 'kg'
                   THEN (ef.end_weight->>'value')::float * 2.20462
                   ELSE (ef.end_weight->>'value')::float END)
      END
    ELSE NULL
  END as weight_loss_lbs,

  -- Weight loss percentage
  CASE
    WHEN (ef.beginning_weight->>'value') IS NOT NULL
      AND (ef.end_weight->>'value') IS NOT NULL
      AND (ef.beginning_weight->>'value')::float > 0
    THEN
      ((ef.beginning_weight->>'value')::float - (ef.end_weight->>'value')::float) /
      (ef.beginning_weight->>'value')::float * 100
    ELSE NULL
  END as weight_loss_percentage,

  -- Weight unit
  (ef.beginning_weight->>'unit') as weight_unit,

  -- Age bucket for demographics
  CASE
    WHEN ef.age IS NULL THEN 'unknown'
    WHEN ef.age BETWEEN 18 AND 29 THEN '18-29'
    WHEN ef.age BETWEEN 30 AND 39 THEN '30-39'
    WHEN ef.age BETWEEN 40 AND 49 THEN '40-49'
    WHEN ef.age BETWEEN 50 AND 59 THEN '50-59'
    WHEN ef.age >= 60 THEN '60+'
    ELSE 'unknown'
  END as age_bucket

FROM extracted_features ef
LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
-- Join to get subreddit from comment's parent post
LEFT JOIN reddit_posts rc_sub ON rc.post_id = rc_sub.post_id;

-- Create indexes for common queries
CREATE INDEX idx_mv_exp_primary_drug ON mv_experiences_denormalized(primary_drug);
CREATE INDEX idx_mv_exp_subreddit ON mv_experiences_denormalized(subreddit);
CREATE INDEX idx_mv_exp_processed_at ON mv_experiences_denormalized(processed_at);
CREATE INDEX idx_mv_exp_age_bucket ON mv_experiences_denormalized(age_bucket);
CREATE INDEX idx_mv_exp_state ON mv_experiences_denormalized(state);
CREATE INDEX idx_mv_exp_country ON mv_experiences_denormalized(country);
CREATE INDEX idx_mv_exp_sex ON mv_experiences_denormalized(sex);
```

**Refresh Strategy:**
```sql
-- Refresh materialized view (run periodically or on-demand)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized;
```

**Benefits:**
- Single query joins all 3 tables
- Pre-calculated weight loss fields
- Pre-bucketed age ranges
- Indexed for fast filtering
- Subreddit field available for Reddit links

---

## tRPC Implementation Structure

### Directory Structure
```
apps/
├── backend/                    # NEW
│   ├── src/
│   │   ├── server.ts          # Express + tRPC server
│   │   ├── trpc.ts            # tRPC initialization
│   │   ├── routers/           # API routers
│   │   │   ├── index.ts       # Root router
│   │   │   ├── drugs.ts       # Drug statistics
│   │   │   ├── experiences.ts # Experience listing
│   │   │   ├── locations.ts   # Geographic data
│   │   │   ├── demographics.ts# Demographics
│   │   │   ├── platform.ts    # Platform stats
│   │   │   ├── trends.ts      # Time-series data
│   │   │   └── predictions.ts # Personalized predictions
│   │   ├── services/          # Business logic
│   │   │   ├── drugStats.ts
│   │   │   ├── experienceFiltering.ts
│   │   │   └── predictions.ts
│   │   └── prisma/
│   │       └── schema.prisma  # Prisma schema
│   ├── package.json
│   └── tsconfig.json
└── frontend/
    └── lib/
        └── trpc.ts            # tRPC client setup
```

### Prisma Schema

**File:** `apps/backend/src/prisma/schema.prisma`

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Materialized view - read-only
model ExperienceDenormalized {
  id                      String    @id @default(uuid())
  post_id                 String?
  comment_id              String?
  subreddit               String?
  reddit_author           String?
  reddit_created_utc      DateTime?
  reddit_score            Int?
  summary                 String
  beginning_weight        Json?
  end_weight              Json?
  duration_weeks          Int?
  cost_per_month          Decimal?  @db.Decimal(10, 2)
  currency                String?
  drugs_mentioned         String[]
  primary_drug            String?
  drug_sentiments         Json?
  sentiment_pre           Decimal?  @db.Decimal(3, 2)
  sentiment_post          Decimal?  @db.Decimal(3, 2)
  recommendation_score    Decimal?  @db.Decimal(3, 2)
  has_insurance           Boolean?
  insurance_provider      String?
  side_effects            Json?
  comorbidities           String[]
  location                String?
  age                     Int?
  sex                     String?
  state                   String?
  country                 String?
  dosage_progression      String?
  exercise_frequency      String?
  dietary_changes         String?
  previous_weight_loss_attempts String[]
  drug_source             String?
  switching_drugs         String?
  side_effect_timing      String?
  side_effect_resolution  Decimal?  @db.Decimal(3, 2)
  food_intolerances       String[]
  plateau_mentioned       Boolean?
  rebound_weight_gain     Boolean?
  labs_improvement        String[]
  medication_reduction    String[]
  nsv_mentioned           String[]
  support_system          String?
  pharmacy_access_issues  Boolean?
  mental_health_impact    String?
  model_used              String
  confidence_score        Decimal?  @db.Decimal(3, 2)
  processed_at            DateTime

  // Calculated fields
  weight_loss_lbs         Decimal?  @db.Decimal(10, 2)
  weight_loss_percentage  Decimal?  @db.Decimal(5, 2)
  weight_unit             String?
  age_bucket              String?

  @@map("mv_experiences_denormalized")
  @@index([primary_drug])
  @@index([subreddit])
  @@index([processed_at])
  @@index([age_bucket])
  @@index([state])
  @@index([country])
  @@index([sex])
}

// Original tables (for reference, not used directly in tRPC)
model RedditPost {
  post_id        String   @id
  subreddit      String
  author         String
  title          String
  selftext       String?
  created_utc    DateTime
  score          Int
  num_comments   Int?
  url            String?
  ingested_at    DateTime @default(now())

  @@map("reddit_posts")
}

model RedditComment {
  comment_id     String   @id
  post_id        String
  parent_id      String?
  author         String
  body           String
  created_utc    DateTime
  score          Int
  ingested_at    DateTime @default(now())

  @@map("reddit_comments")
}

model ExtractedFeature {
  id                      String    @id @default(uuid())
  post_id                 String?
  comment_id              String?
  // ... all fields same as materialized view

  @@map("extracted_features")
}
```

---

## tRPC Router Implementations

### 1. Platform Router
**File:** `apps/backend/src/routers/platform.ts`

```typescript
import { router, publicProcedure } from '../trpc';
import { prisma } from '../prisma/client';

export const platformRouter = router({
  getStats: publicProcedure.query(async () => {
    const [totalExperiences, uniqueDrugs, statsData, uniqueStates, uniqueCountries] = await Promise.all([
      // Total experiences
      prisma.experienceDenormalized.count(),

      // Unique drugs
      prisma.experienceDenormalized.findMany({
        where: { primary_drug: { not: null } },
        select: { primary_drug: true },
        distinct: ['primary_drug'],
      }),

      // Average weight loss
      prisma.experienceDenormalized.aggregate({
        _avg: { weight_loss_percentage: true },
        where: { weight_loss_percentage: { not: null } },
      }),

      // Unique states
      prisma.experienceDenormalized.findMany({
        where: { state: { not: null } },
        select: { state: true },
        distinct: ['state'],
      }),

      // Unique countries
      prisma.experienceDenormalized.findMany({
        where: { country: { not: null } },
        select: { country: true },
        distinct: ['country'],
      }),
    ]);

    return {
      totalExperiences,
      totalDrugs: uniqueDrugs.length,
      avgWeightLoss: Number(statsData._avg.weight_loss_percentage?.toFixed(1) || 0),
      statesTracked: uniqueStates.length,
      countriesTracked: uniqueCountries.length,
    };
  }),
});
```

### 2. Drugs Router
**File:** `apps/backend/src/routers/drugs.ts`

```typescript
import { router, publicProcedure } from '../trpc';
import { z } from 'zod';
import { prisma } from '../prisma/client';
import type { Prisma } from '@prisma/client';

export const drugsRouter = router({
  getAllStats: publicProcedure.query(async () => {
    // Get all drugs with experience counts
    const drugCounts = await prisma.experienceDenormalized.groupBy({
      by: ['primary_drug'],
      where: { primary_drug: { not: null } },
      _count: true,
      orderBy: { _count: { primary_drug: 'desc' } },
    });

    // For each drug, calculate detailed stats
    const drugStats = await Promise.all(
      drugCounts.map(async ({ primary_drug, _count }) => {
        // Aggregated numeric stats
        const aggregates = await prisma.experienceDenormalized.aggregate({
          where: { primary_drug },
          _avg: {
            weight_loss_percentage: true,
            weight_loss_lbs: true,
            duration_weeks: true,
            cost_per_month: true,
            sentiment_pre: true,
            sentiment_post: true,
            recommendation_score: true,
          },
          _count: {
            has_insurance: true,
          },
        });

        // Insurance coverage rate
        const insuranceCount = await prisma.experienceDenormalized.count({
          where: { primary_drug, has_insurance: true },
        });

        // Pharmacy access issues rate
        const accessIssuesCount = await prisma.experienceDenormalized.count({
          where: { primary_drug, pharmacy_access_issues: true },
        });

        // Plateau rate
        const plateauCount = await prisma.experienceDenormalized.count({
          where: { primary_drug, plateau_mentioned: true },
        });

        // Rebound rate
        const reboundCount = await prisma.experienceDenormalized.count({
          where: { primary_drug, rebound_weight_gain: true },
        });

        // Side effects aggregation (JSONB parsing required)
        // This requires raw SQL for efficient JSONB processing
        const sideEffects = await prisma.$queryRaw<Array<{ name: string; count: number }>>`
          SELECT
            se->>'name' as name,
            COUNT(*) as count
          FROM mv_experiences_denormalized,
            jsonb_array_elements(side_effects) se
          WHERE primary_drug = ${primary_drug}
          GROUP BY se->>'name'
          ORDER BY count DESC
          LIMIT 10
        `;

        // Drug sources
        const drugSources = await prisma.experienceDenormalized.groupBy({
          by: ['drug_source'],
          where: { primary_drug, drug_source: { not: null } },
          _count: true,
        });

        return {
          drug: primary_drug!,
          count: _count,
          avgWeightLoss: Number(aggregates._avg.weight_loss_percentage?.toFixed(1)) || null,
          avgWeightLossLbs: Number(aggregates._avg.weight_loss_lbs?.toFixed(1)) || null,
          avgDurationWeeks: Number(aggregates._avg.duration_weeks?.toFixed(0)) || null,
          avgCostPerMonth: Number(aggregates._avg.cost_per_month?.toFixed(0)) || null,
          avgSentimentPre: Number(aggregates._avg.sentiment_pre?.toFixed(2)) || null,
          avgSentimentPost: Number(aggregates._avg.sentiment_post?.toFixed(2)) || null,
          avgRecommendationScore: Number(aggregates._avg.recommendation_score?.toFixed(2)) || null,
          insuranceCoverage: Math.round((insuranceCount / _count) * 100),
          commonSideEffects: sideEffects.map(se => ({
            name: se.name,
            count: Number(se.count),
            percentage: Math.round((Number(se.count) / _count) * 100),
          })),
          sideEffectSeverity: {
            mild: 0, // TODO: Calculate from JSONB severity field
            moderate: 0,
            severe: 0,
          },
          drugSources: {
            brand: drugSources.find(ds => ds.drug_source === 'brand')?._count || 0,
            compounded: drugSources.find(ds => ds.drug_source === 'compounded')?._count || 0,
            outOfPocket: drugSources.find(ds => ds.drug_source === 'out-of-pocket')?._count || 0,
            other: drugSources.find(ds => ds.drug_source === 'other')?._count || 0,
          },
          pharmacyAccessIssues: Math.round((accessIssuesCount / _count) * 100),
          plateauRate: Math.round((plateauCount / _count) * 100),
          reboundRate: Math.round((reboundCount / _count) * 100),
        };
      })
    );

    return drugStats;
  }),

  getStats: publicProcedure
    .input(z.object({ drug: z.string() }))
    .query(async ({ input }) => {
      // Similar logic to getAllStats but for single drug
      // ... implementation
    }),
});
```

### 3. Experiences Router
**File:** `apps/backend/src/routers/experiences.ts`

```typescript
import { router, publicProcedure } from '../trpc';
import { z } from 'zod';
import { prisma } from '../prisma/client';

export const experiencesRouter = router({
  list: publicProcedure
    .input(
      z.object({
        drug: z.string().optional(),
        search: z.string().optional(),
        limit: z.number().min(1).max(100).default(20),
        offset: z.number().min(0).default(0),
      })
    )
    .query(async ({ input }) => {
      const { drug, search, limit, offset } = input;

      const where: Prisma.ExperienceDenormalizedWhereInput = {
        AND: [
          drug && drug !== 'all' ? { primary_drug: drug } : {},
          search ? { summary: { contains: search, mode: 'insensitive' } } : {},
        ],
      };

      const [experiences, total] = await Promise.all([
        prisma.experienceDenormalized.findMany({
          where,
          select: {
            id: true,
            post_id: true,
            comment_id: true,
            summary: true,
            primary_drug: true,
            weight_loss_lbs: true,
            weight_loss_percentage: true,
            weight_unit: true,
            duration_weeks: true,
            sentiment_post: true,
            recommendation_score: true,
            side_effects: true, // Will need to parse top 3
            cost_per_month: true,
            age: true,
            sex: true,
            location: true,
            processed_at: true,
          },
          orderBy: { processed_at: 'desc' },
          take: limit,
          skip: offset,
        }),
        prisma.experienceDenormalized.count({ where }),
      ]);

      // Transform to ExperienceCard format
      const cards = experiences.map(exp => {
        // Parse side effects JSONB to get top 3
        const sideEffects = (exp.side_effects as any[]) || [];
        const topSideEffects = sideEffects
          .slice(0, 3)
          .map(se => se.name);

        return {
          id: exp.id,
          post_id: exp.post_id,
          comment_id: exp.comment_id,
          summary: exp.summary,
          primary_drug: exp.primary_drug,
          weightLoss: exp.weight_loss_lbs ? Number(exp.weight_loss_lbs) : null,
          weightLossUnit: exp.weight_unit as 'lbs' | 'kg' | null,
          duration_weeks: exp.duration_weeks,
          sentiment_post: exp.sentiment_post ? Number(exp.sentiment_post) : null,
          recommendation_score: exp.recommendation_score ? Number(exp.recommendation_score) : null,
          top_side_effects: topSideEffects,
          cost_per_month: exp.cost_per_month ? Number(exp.cost_per_month) : null,
          age: exp.age,
          sex: exp.sex,
          location: exp.location,
          processed_at: exp.processed_at.toISOString(),
        };
      });

      return { experiences: cards, total };
    }),
});
```

### 4. Other Routers
Similar implementations for:
- `locations.ts` - Geographic data
- `demographics.ts` - Age/sex/comorbidity distributions
- `trends.ts` - Time-series data
- `predictions.ts` - ML-based recommendations

---

## Frontend Integration

### tRPC Client Setup
**File:** `apps/frontend/lib/trpc.ts`

```typescript
import { createTRPCReact } from '@trpc/react-query';
import type { AppRouter } from '../../../backend/src/routers';

export const trpc = createTRPCReact<AppRouter>();
```

### Provider Setup
**File:** `apps/frontend/app/providers.tsx`

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { httpBatchLink } from '@trpc/client';
import { useState } from 'react';
import { trpc } from '@/lib/trpc';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        httpBatchLink({
          url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/trpc',
        }),
      ],
    })
  );

  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </trpc.Provider>
  );
}
```

### Replace Mock Data
**Example:** `apps/frontend/app/compare/page.tsx`

```typescript
// OLD:
import { getAllDrugStats } from "@/lib/mock-data"
const stats = await getAllDrugStats()

// NEW:
import { trpc } from '@/lib/trpc'
const { data: stats, isLoading } = trpc.drugs.getAllStats.useQuery()
```

---

## Implementation Checklist

1. **Database:**
   - [ ] Create materialized view migration
   - [ ] Run migration on Supabase
   - [ ] Set up refresh cron job

2. **Backend:**
   - [ ] Initialize Node.js backend project
   - [ ] Install dependencies (tRPC, Prisma, Express, Zod)
   - [ ] Configure Prisma schema
   - [ ] Implement tRPC routers
   - [ ] Set up Express server
   - [ ] Deploy to Railway

3. **Frontend:**
   - [ ] Install tRPC client dependencies
   - [ ] Set up tRPC provider
   - [ ] Replace mock data in all pages
   - [ ] Test all pages with real data
   - [ ] Handle loading states
   - [ ] Handle error states

4. **Optimization:**
   - [ ] Add Redis caching for expensive queries
   - [ ] Optimize JSONB parsing queries
   - [ ] Set up materialized view auto-refresh
   - [ ] Monitor query performance

---

## Next Steps

1. Create materialized view SQL migration
2. Set up backend directory structure
3. Implement tRPC routers
4. Integrate with frontend
5. Deploy and test
