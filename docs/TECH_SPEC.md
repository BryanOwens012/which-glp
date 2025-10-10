# WhichGLP Technical Specification

**Project:** WhichGLP
**Domain:** whichglp.com
**Purpose:** Real-world GLP-1 weight-loss drug outcomes aggregation platform
**Data Sources:** Reddit API, Twitter API, user-submitted reviews (future)

---

## Table of Contents

1. [Major Drugs to Track](#major-drugs-to-track)
2. [Data Sources](#data-sources)
3. [Tech Stack](#tech-stack)
4. [Data Extraction & Processing Pipeline](#data-extraction--processing-pipeline)

---

## Major Drugs to Track

### FDA-Approved GLP-1 Agonists (September 2025)

**Tier 1: Most Prescribed (Primary Focus)**

1. **Semaglutide**
   - **Brand Names:** Ozempic (diabetes), Wegovy (weight loss), Rybelsus (oral diabetes)
   - **Manufacturer:** Novo Nordisk
   - **Mechanism:** GLP-1 receptor agonist
   - **Dosing:** Weekly injection (Ozempic/Wegovy) or daily oral (Rybelsus)
   - **Efficacy:** 15.1% average weight loss at 68 weeks (OASIS 1 trial)
   - **Cost:** ~$1,200-1,500/month retail, $13,600/year (Kaiser estimate)
   - **FDA Approvals:** Diabetes (2017), obesity (2021), cardiovascular risk reduction (2024), chronic kidney disease (Jan 2025)
   - **Reddit Presence:** r/Ozempic (140K members), r/Wegovy (80K members), r/semaglutide (45K members)

2. **Tirzepatide**
   - **Brand Names:** Mounjaro (diabetes), Zepbound (weight loss)
   - **Manufacturer:** Eli Lilly
   - **Mechanism:** Dual GLP-1/GIP receptor agonist (more potent than semaglutide)
   - **Dosing:** Weekly injection
   - **Efficacy:** Up to 22.5% average weight loss at 72 weeks (SURMOUNT trials)
   - **Cost:** ~$1,000-1,200/month retail, LillyDirect offers $550-650/month cash pay
   - **FDA Approvals:** Diabetes (2022), obesity (2023), obstructive sleep apnea (Dec 2024)
   - **Reddit Presence:** r/Mounjaro (85K members), r/zepbound (62K members), r/tirzepatidecompound (28K members)

3. **Liraglutide**
   - **Brand Names:** Victoza (diabetes), Saxenda (weight loss)
   - **Manufacturer:** Novo Nordisk
   - **Mechanism:** GLP-1 receptor agonist (older generation)
   - **Dosing:** Daily injection
   - **Efficacy:** 8% average weight loss (lower than newer drugs)
   - **Cost:** ~$1,400/month retail, **generic available since Dec 2024 (~$600/month)**
   - **FDA Approvals:** Diabetes (2010), obesity (2014)
   - **Reddit Presence:** r/liraglutide (12K members), often discussed in r/GLP1Agonists

**Tier 2: Less Common but FDA-Approved**

4. **Dulaglutide (Trulicity)**
   - Weekly injection for diabetes, not approved for weight loss
   - Moderate weight loss as side effect (~5-7%)
   - Generic expected 2027

5. **Exenatide (Byetta, Bydureon)**
   - Older GLP-1, less effective than semaglutide/tirzepatide
   - Generic available (Amneal, Nov 2024)
   - Limited Reddit discussion

6. **Lixisenatide (Adlyxin)**
   - Daily injection for diabetes
   - Minimal weight loss effect
   - Low prescription volume

### Pipeline Drugs (Clinical Trials - Track for Future)

**Phase 3 (Likely Approval 2025-2026):**

1. **Oral Semaglutide 25mg/50mg (Wegovy Oral)**
   - **Manufacturer:** Novo Nordisk
   - **Status:** NDA submitted, FDA decision expected Q4 2025
   - **Efficacy:** 15.1% weight loss at 68 weeks (OASIS 1 trial), superior to 14mg Rybelsus
   - **Value Prop:** First oral GLP-1 for weight loss (no injections)
   - **Monitor:** FDA approval announcement, pricing

2. **Orforglipron**
   - **Manufacturer:** Eli Lilly
   - **Status:** Phase 3 completed early 2025, results expected soon
   - **Mechanism:** Oral GLP-1 receptor agonist
   - **Efficacy:** Up to 14.7% weight loss at 36 weeks (Phase 2)
   - **Value Prop:** Eli Lilly's answer to oral semaglutide

3. **CagriSema**
   - **Manufacturer:** Novo Nordisk
   - **Status:** Phase 3 (REDEFINE 4 trial vs tirzepatide)
   - **Mechanism:** GLP-1 + amylin dual agonist (cagrilintide + semaglutide)
   - **Efficacy:** REDEFINE 1 showed mixed results (fell short of expectations), awaiting REDEFINE 4
   - **Value Prop:** Targeting mid-20% weight loss range to compete with tirzepatide
   - **Risk:** REDEFINE 1 underperformance raises questions

4. **MariTide**
   - **Manufacturer:** Amgen
   - **Status:** Phase 3 started March 2025
   - **Mechanism:** Monoclonal antibody (activates GLP-1, blocks GIP)
   - **Efficacy:** 20% average weight loss at 52 weeks (Phase 2)
   - **Dosing:** Monthly injection (vs weekly for current drugs)
   - **Value Prop:** Less frequent dosing, potentially better adherence

5. **Retatrutide**
   - **Manufacturer:** Eli Lilly
   - **Status:** Phase 3 (likely 2026 launch)
   - **Mechanism:** Triple agonist (GLP-1/GIP/glucagon)
   - **Efficacy:** Up to 24% weight loss reported in Phase 2
   - **Value Prop:** Potentially most effective weight loss drug if approved
   - **Reddit Hype:** High anticipation, but can't be legally compounded

**Phase 2 (Monitor for Progress):**

6. **NN-9932 (Novo Nordisk)** - Oral GLP-1 for obesity, Phase 3 trials ongoing
7. **GSBR-1290 (Structure Therapeutics)** - Oral GLP-1, Phase 2b
8. **Petrelintide (Zealand Pharma)** - Amylin analog, Phase 2
9. **Bimagrumab + Semaglutide (Eli Lilly)** - Muscle preservation combo, Phase 2b

**Track Drug Classes:**
- Single GLP-1 agonists (semaglutide, liraglutide)
- Dual GLP-1/GIP agonists (tirzepatide)
- GLP-1/amylin combinations (CagriSema)
- Triple agonists (retatrutide)
- Oral formulations (emerging category)

---

## Data Sources

### Primary Source: Reddit (via Reddit API)

**API Strategy:**
- **Primary Method:** Reddit API (OAuth 2.0, read-only application)
- **Rate Limits:** 60 requests per minute for OAuth apps (10x better than anonymous)
- **Endpoints:**
  - `/r/{subreddit}/hot` - Real-time trending posts
  - `/r/{subreddit}/top?t=day` - Top posts from past 24 hours
  - `/r/{subreddit}/new` - Newest posts for comprehensive coverage
  - `/comments/{post_id}` - Full post + nested comment threads
- **Authentication:** Register app at reddit.com/prefs/apps, store refresh token
- **Backup:** Playwright scraping if API rate limits exceeded or API access revoked

**Subreddits to Monitor (Priority Order):**

**Tier 1 - Drug-Specific, High Activity:**
1. **r/Ozempic** (140K members) - Semaglutide for diabetes, off-label weight loss
2. **r/Mounjaro** (85K members) - Tirzepatide for diabetes
3. **r/Wegovy** (80K members) - Semaglutide specifically for weight loss
4. **r/zepbound** (62K members) - Tirzepatide specifically for weight loss
5. **r/semaglutide** (45K members) - Generic semaglutide discussions
6. **r/tirzepatidecompound** (28K members) - Generic tirzepatide discussions

**Tier 2 - General GLP-1 Discussions:**
7. **r/glp1** (35K members) - Cross-drug comparisons, general questions
8. **r/ozempicforweightloss** (37K members) - Dedicated Ozempic weight loss community, off-label use focus
9. **r/WegovyWeightLoss** (18K members) - Success stories, tips
10. **r/liraglutide** (12K members) - Older drug, generic now available

**Tier 3 - Broader Weight Loss Communities:**
11. **r/loseit** (4.2M members) - General weight loss, GLP-1 discussions in comments
12. **r/progresspics** (2.8M members) - Before/after photos, GLP-1 mentions in titles/comments
13. **r/intermittentfasting** (965K members) - Fasting community, some GLP-1 discussions
14. **r/1200isplenty** (583K members) - Calorie restriction, occasional GLP-1 mentions
15. **r/fasting** (538K members) - Fasting protocols, GLP-1 sometimes mentioned
16. **r/CICO** (301K members) - Calories in/calories out, weight loss tracking
17. **r/1500isplenty** (293K members) - Moderate calorie restriction
18. **r/PCOS** (251K members) - GLP-1s discussed for PCOS weight management
19. **r/Brogress** (249K members) - Male progress pics and transformations
20. **r/diabetes** (149K members) - General diabetes discussions, GLP-1 mentions
21. **r/obesity** (120K members) - Medical obesity discussions
22. **r/peptides** (121K members) - Peptide discussions including GLP-1 compounds
23. **r/SuperMorbidlyObese** (90K members) - Higher BMI users, often discuss GLP-1s
24. **r/diabetes_t2** (49K members) - Type 2 diabetes, GLP-1s commonly prescribed

**Tier 4 - Counter-Cultural & Critical Perspectives (Future Consideration):**
*Note: Not actively monitored yet, but identified for bias mitigation and representativeness*

25. **r/medicine** - Medical professionals discussing pros/cons, clinical concerns, professional skepticism
26. **r/AskDocs** - Pre-medication concerns, side effect questions, medical advice seeking
27. **r/antidiet** - Anti-diet culture movement, philosophical opposition to medicalized weight loss
28. **r/chronicillness** - Long-term side effect discussions, quality of life impact
29. **r/povertyfinance** or **r/personalfinance** - Cost/access barriers, financial burden discussions

**Rationale for Tier 4:**
- **Selection Bias Mitigation:** Drug-specific subreddits may over-represent positive experiences
- **Broader Context:** Capture financial concerns, philosophical opposition, and long-term health impacts
- **Professional Perspective:** Medical community discussions provide clinical reality checks
- **Not Actively Ingested:** Dataset size is sufficient for now; revisit when expanding to 100K+ data points

**Content Types to Extract:**
- **Original Posts:** Personal experiences, progress updates, questions
- **Comments:** Answers to cost/side effect/efficacy questions
- **Weekly Discussion Threads:** Consolidated experiences
- **AMA Threads:** Doctors, pharmacists, patients with long-term experience

**Ingestion Strategy:**
- **Real-Time Stream:** Poll /hot and /new every 5 minutes (Tier 1 subreddits)
- **Daily Batch:** Top 50 posts from past 24 hours (all Tier 1 subreddits)
- **Weekly Batch:** Top 200 posts from past 7 days (Tier 1 + Tier 2)
- **Monthly Historical:** Top posts from past month (Tier 3, selective)
- **Comment Ingestion:** Full comment tree for each post (Reddit API provides nested structure)
- **Deduplication:** Store post ID (e.g., `t3_abc123`) as unique key

**API Response Handling:**
- Parse JSON responses directly (no HTML parsing needed)
- Extract: post_id, subreddit, author, created_utc, title, selftext, score, num_comments
- For comments: comment_id, parent_id, body, author, created_utc, score
- Handle deleted/removed content gracefully (author shows as "[deleted]")

### Secondary Source: Twitter/X (via twitterapi.io)

**API Strategy:**
- **Primary Method:** twitterapi.io (third-party Twitter API proxy)
- **Why twitterapi.io:** Official Twitter API v2 pricing prohibitive ($5,000/month for historical search), twitterapi.io offers $49-199/month tiers
- **Endpoints:**
  - `/tweets/search` - Keyword search with filters
  - `/tweets/{tweet_id}` - Individual tweet details
  - `/tweets/{tweet_id}/replies` - Reply threads
- **Rate Limits:** Varies by plan (check twitterapi.io documentation)
- **Backup:** Playwright scraping if API access fails or costs exceed budget

**Search Queries to Monitor:**
- **Drug Names:** "Ozempic", "Wegovy", "Mounjaro", "Zepbound", "GLP-1", "semaglutide", "tirzepatide"
- **Experience Keywords:** "lost weight on", "side effects", "cost", "insurance", "progress", "before and after"
- **Comparison Phrases:** "vs", "better than", "switching from", "tried both"
- **Hashtags:** #Ozempic, #GLP1, #WeightLossJourney, #Mounjaro, #Wegovy

**Content Types:**
- Personal progress updates with weight numbers
- Cost complaints/celebrations
- Side effect discussions
- Before/after text descriptions (no image storage)
- Insurance coverage experiences

**Ingestion Strategy:**
- **Real-Time Stream:** Poll every 15 minutes for new tweets matching queries
- **Daily Batch:** Tweets from past 24 hours with engagement filter (min 10 likes/retweets)
- **Engagement Filtering:** Reduce spam by requiring minimum interaction
- **Deduplication:** Store tweet ID as unique key
- **Reply Threading:** Fetch replies to high-engagement tweets for additional context

**API Response Handling:**
- Parse JSON responses
- Extract: tweet_id, author, created_at, text, like_count, retweet_count, reply_count
- Handle rate limits with exponential backoff
- Filter out promotional content (accounts with "ad" disclosures, multiple product links)

**Challenges:**
- Twitter less structured than Reddit (harder to extract structured data)
- More promotional/spam content (requires aggressive filtering)
- Shorter character limit (280 chars) = less detail than Reddit posts
- Consider lower priority than Reddit initially

### Backup: Playwright Web Scraping

**When to Use:**
- Reddit API rate limits exceeded (>60 req/min)
- Reddit OAuth revoked or application suspended
- twitterapi.io service outage or rate limits exceeded
- Cost optimization (avoid paying for API if scraping sufficient)

**Scraping Architecture:**
- **Tool:** Playwright with Chromium headless browser
- **Why Playwright:** Reddit/Twitter use JavaScript for lazy-loading, infinite scroll
- **Rate Limiting:** Redis-based limiter (1 request per 2 seconds per domain)
- **User Agent Rotation:** Mimic real browsers, avoid detection
- **Proxy Rotation:** Residential proxies if IP bans occur
- **Error Handling:** Exponential backoff, retry 3x, log failures

**Scraping Process (Reddit):**
1. Navigate to subreddit sorted by "hot" or "top" (past 24 hours)
2. Scroll to load posts (handle infinite scroll with `page.evaluate`)
3. Extract post metadata: title, author, date, upvotes, URL, subreddit
4. Click into post to load full content + comments
5. Extract post body (markdown/HTML conversion needed)
6. Extract comment threads (handle nested structure manually)
7. Store raw content in ScrapedReview table
8. Mark for AI processing

**Scraping Process (Twitter):**
1. Navigate to Twitter search with query
2. Scroll to load tweets (infinite scroll)
3. Extract tweet metadata: author, date, text, likes, retweets
4. Click into tweet to load replies (if high engagement)
5. Extract reply threads
6. Store raw content in ScrapedReview table

**Deduplication:**
- Reddit: Store post URL as unique key (e.g., `reddit.com/r/Ozempic/comments/abc123`)
- Twitter: Store tweet URL as unique key (e.g., `twitter.com/user/status/1234567890`)

### Tertiary Source: User-Submitted Reviews (Future)

**Phase 2-3 Feature:**
- Allow authenticated users to submit structured reviews directly
- Multi-step form with validation (drug, weight, duration, cost, side effects)
- Email verification required for submission
- Manual review queue for suspicious data (extreme claims, duplicate text)

**Why Start with API/Scraped Data:**
- Cold start problem: Need seed data to attract users
- API ingestion provides volume quickly (thousands of posts per day)
- User submissions more reliable but slower to accumulate
- Hybrid approach: API data for breadth, user data for depth

---

## Tech Stack

### Frontend Service

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **UI:** React 19, Tailwind CSS v4, Radix UI + shadcn/ui
- **API Client:** tRPC client, TanStack Query
- **Hosting:** Vercel

### Backend Services

**1. API Service** (`apps/api`)
- **Runtime:** Node.js 20+
- **Language:** TypeScript (strict mode)
- **Framework:** tRPC (type-safe API)
- **Database:** Supabase client
- **Caching:** Redis (ioredis)

**2. Post Ingestion** (`apps/post-ingestion`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **Data Source:** Reddit API (PRAW)
- **Database:** Supabase client
- **Function:** Fetch recent Reddit posts from GLP-1 subreddits

**3. Post Extraction** (`apps/post-extraction`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **Database:** Supabase client
- **AI Model:** GLM-4.5-Air (via Z.ai SDK)
- **Function:** Extract structured drug experience data from posts

**4. User Extraction** (`apps/user-extraction`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **Database:** Supabase client
- **AI Model:** GLM-4.5-Air (via Z.ai SDK)
- **Function:** Extract user demographics from Reddit user history

**5. Recommendation Engine** (`apps/rec-engine`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **ML Stack:** scikit-learn (KNN), pandas, numpy
- **Database:** Supabase client
- **Function:** Generate personalized drug recommendations

### Infrastructure

**Vercel**
- **Frontend:** Next.js app

**Railway** (9 services total)
- **Core Services:**
  - Redis (caching with persistent volume)
  - API (tRPC gateway)
  - Rec-Engine (ML recommendations)
- **Data Pipeline Services:**
  - Post-Ingestion (Reddit post fetching)
  - Post-Extraction (AI drug experience extraction)
  - User-Extraction (AI user demographics extraction)
- **Cron Jobs (Automated Scheduling):**
  - View-Refresher-Cron (refreshes materialized views every 45 minutes)
  - Post-Ingestion-Cron (triggers Reddit ingestion every 16 hours)
  - Post-Extraction-Cron (triggers AI extraction every 22 hours)
  - User-Extraction-Cron (triggers user analysis daily)

**Supabase**
- **Database:** PostgreSQL

### Architecture Notes

- **Primary ingestion:** Reddit API (PRAW) via scheduled cron jobs
- **Type safety:** tRPC ensures frontend/backend contract enforcement
- **AI Processing:** GLM-4.5-Air (cost-effective alternative to Claude Sonnet 4)
- **Automated Pipeline:** Cron jobs orchestrate the data ingestion → extraction → view refresh cycle
- **Microservices:** Each service independently scalable on Railway

---

## Data Extraction & Processing Pipeline

### Ingestion Architecture

**Primary: API-Based Ingestion**

**Reddit API Client:**
- **Library:** PRAW (Python Reddit API Wrapper) or custom HTTP client
- **Authentication:** OAuth 2.0 with client credentials flow
- **Polling Frequency:**
  - Real-time: Poll /hot and /new every 5 minutes (Tier 1 subreddits)
  - Batch: Fetch top posts daily/weekly (Tier 2/3 subreddits)
- **Data Storage:** Store raw JSON response in `ScrapedReview` table with `source='reddit_api'`
- **Error Handling:** Log API errors, switch to Playwright backup if consecutive failures

**Twitter API Client (via twitterapi.io):**
- **Library:** requests (Python) for HTTP calls to twitterapi.io
- **Authentication:** API key-based (twitterapi.io credentials)
- **Polling Frequency:**
  - Real-time: Poll search endpoint every 15 minutes
  - Batch: Fetch historical tweets daily
- **Data Storage:** Store raw JSON response in `ScrapedReview` table with `source='twitter_api'`
- **Error Handling:** Retry with exponential backoff, switch to Playwright if API unavailable

**Fallback: Playwright Scraping**
- Activate when API rate limits exceeded or access denied
- Use same database schema (`source='reddit_scrape'` or `source='twitter_scrape'`)
- Implement rotating proxies and user agents for reliability

**Rate Limiting:**
- Redis-based distributed rate limiter
- Track API calls per minute/hour per source
- Automatic throttling when approaching limits
- Alert if consistently hitting rate limits (consider upgrading API tier)

**Deduplication:**
- Reddit: Use `post_id` (e.g., `t3_abc123`) as unique key
- Twitter: Use `tweet_id` as unique key
- Check existence before inserting into database
- Handle cross-posts: Store all URLs where content appears

### AI Extraction Pipeline

**Goal:** Convert unstructured post/comment text into structured data

**Extraction Model:** GLM-4.5-Air (via Z.ai SDK) - cost-effective model for text extraction, summarization, and sentiment analysis

**Process:**
1. Query unprocessed posts/comments from database
2. Build context for each item (parent post, parent comments, top replies)
3. Send to GLM-4.5-Air API with structured extraction prompt
4. Parse JSON response into database schema
5. Store extracted features in `extracted_features` table
6. Backup extraction results to JSON files

**Extracted Features:**
- Drug name (Ozempic, Wegovy, Mounjaro, etc.)
- Weight loss amount and timeframe
- Starting weight and current weight
- Cost (monthly, out-of-pocket, insurance coverage status)
- Side effects (nausea, vomiting, fatigue, constipation, etc.)
- Demographics (age, sex, location if mentioned)
- Insurance provider
- Sentiment (positive, negative, neutral)
