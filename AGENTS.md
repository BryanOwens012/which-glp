# WhichGLP Technical Stack & Architecture - AGENTS.md

## Project Overview

**Project Name:** WhichGLP  
**Domain:** whichglp.com  
**Purpose:** Aggregation and analysis platform for weight-loss drug (GLP-1 agonist) reviews and real-world outcomes  
**Data Sources:** Reddit posts/comments (Reddit API), Twitter posts (Twitter API via twitterapi.io), user-submitted reviews (future)  
**Target Users:** General public researching weight-loss medications (non-technical, unfamiliar with drugs/biotech/medical terminology)

### Mission Statement
WhichGLP creates the definitive real-world dataset for GLP-1 weight-loss drug outcomes by aggregating thousands of anonymous user experiences from social media, structuring unstructured text data, and providing personalized predictions that generic LLMs cannot generate.

---

## Why WhichGLP Exists: The Value Proposition Gap

### What LLMs Cannot Provide

**1. Proprietary Real-World Dataset**
- LLMs trained on public data lack access to recent (2024-2025) Reddit/Twitter discussions
- No structured database of real user outcomes (weight loss amounts, timeframes, costs by geography)
- No aggregated statistics across thousands of real users
- WhichGLP builds exclusive dataset by continuous API ingestion + AI extraction

**2. Location-Specific Intelligence**
- Cost variations by state, insurance provider, pharmacy
- Provider availability by city (NYC vs SF vs Charlotte vs. rural areas)
- Insurance coverage patterns by employer/region
- International pricing differences (US vs Canada vs UK)

**3. Personalized Outcome Predictions**
- "Based on 500+ users with your profile (male, 28, 200lbs, NYC, Aetna insurance), you can expect:"
  - 15-18% weight loss in 6 months on Zepbound
  - $180-220/month out-of-pocket cost
  - 25% probability of mild nausea (first 2 weeks)
- LLMs give generic ranges; WhichGLP gives cohort-specific predictions

**4. Real-Time Market Intelligence**
- Live drug shortage tracking (compounded vs branded availability)
- Price fluctuations across pharmacies/regions
- New drug launches and clinical trial readouts
- Insurance coverage policy changes
- Reddit/Twitter sentiment trends (which drugs are gaining/losing favor)

**5. Decision-Making Tools LLMs Cannot Provide**
- Interactive comparison: "Show me drugs under $150/month with <10% nausea rate achieving >15% weight loss"
- ROI calculator: "Is $300/month drug worth it vs $150/month drug with 5% less efficacy?"
- Provider finder: "GLP-1 prescribers in Palo Alto accepting new patients, sorted by Reddit mentions"
- Timeline calculator: "How long to lose 40lbs on Wegovy based on users starting at 220lbs?"

**6. Community-Driven Insights**
- Peer matching: "Users who started Mounjaro at 195lbs in Q1 2025"
- Reddit thread rankings: Most helpful posts about specific drugs
- Side effect management strategies from real users
- Insurance appeal success stories with templates

### The Moat: Network Effects in Data

**Data Compound Value:**
- More API-ingested posts → better AI extraction patterns → more accurate predictions
- More users → more demographic segments → better personalization
- More cost data → precise insurance coverage mapping → better cost predictions
- More time-series data → weight loss trajectory modeling → accurate timeline predictions

**Think:**
- **Glassdoor** for salaries → **WhichGLP** for drug outcomes
- **Goodreads** for books → **WhichGLP** for medications
- **TripAdvisor** for hotels → **WhichGLP** for treatments

The value is in the exclusive, structured, continuously-updated dataset that gets exponentially more useful with scale.

---

## Market Context (September 28, 2025)

### Market Size & Growth Trajectory

**Current Market (2025):**
- Global weight-loss drug market: $50-60 billion annually
- Projected 2030: $100-150 billion (Goldman Sachs, Morgan Stanley estimates)
- Projected 2035: $150 billion+ with expanded indications
- More than 2% of U.S. adults (6.6 million people) took GLP-1 for weight loss in 2024
- 26% of U.S. adults plan to take weight loss drug in 2025 (eMarketer)

**Growth Drivers:**
- FDA expanding approved indications (heart failure, sleep apnea, MASH liver disease, chronic kidney disease)
- Insurance coverage expansion (40 million Americans now have coverage vs 37 million diabetics)
- Social media normalization (TikTok, Instagram before/after content)
- Supply stabilization after 2022-2024 shortages
- Oral formulations launching (Rybelsus currently, Oral Wegovy expected Q4 2025)
- Competition driving prices down (generic liraglutide launched Dec 2024)

### Critical Market Events (2024-2025 Timeline)

**December 19, 2024:** FDA removes tirzepatide (Zepbound/Mounjaro) from shortage list  
**December 21, 2024:** Generic liraglutide (Victoza) becomes commercially available in US  
**February 21, 2025:** FDA removes semaglutide (Wegovy/Ozempic) from shortage list  
**March 2025:** Amgen's MariTide enters Phase 3 trials (showed 20% weight loss at 52 weeks)  
**May 22, 2025:** Compounded GLP-1s become illegal, forcing 1M+ patients to branded drugs  
**Q3 2025 (expected):** Wegovy approval for MASH (metabolic liver disease)  
**Q4 2025 (expected):** Oral Wegovy 25mg/50mg approval for weight loss  

**Discontinuation Crisis:**
- 60-64% of patients discontinue due to cost/loss of insurance coverage (Goldman Sachs survey)
- 15% discontinue due to GI side effects (nausea, vomiting, diarrhea)
- 50% drop-out rate overall creates massive need for comparison/cost transparency tools

### Competitive Landscape: Why Now?

**No Direct Competitors Exist Yet:**
- **Drugs.com, WebMD:** Clinical information, not real-world outcomes or cost data
- **GoodRx:** Pharmacy price comparison, but no efficacy/side effect data
- **Reddit/Twitter:** Unstructured discussions, impossible to compare or analyze at scale
- **Clinical trials:** Controlled settings, not representative of real-world use
- **Pharma websites:** Marketing materials, biased data, no peer comparisons

**WhichGLP's First-Mover Advantage:**
- Build dataset before competitors recognize opportunity
- Establish SEO dominance for high-intent keywords ("Zepbound vs Wegovy cost")
- Network effects: First to aggregate creates strongest dataset
- Brand recognition: Become "the Glassdoor of GLP-1s"

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

## Data Sources: Where Reviews Come From

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
- **Selection Bias Mitigation:** Drug-specific subreddits may over-represent positive experiences (though 65-75% discontinuation rate suggests negative experiences ARE captured)
- **Broader Context:** Capture financial concerns, philosophical opposition, and long-term health impacts not discussed in drug-enthusiast communities
- **Professional Perspective:** Medical community discussions provide clinical reality checks
- **Not Actively Ingested:** Dataset size is sufficient for now; revisit when expanding to 100K+ data points or when bias analysis shows gaps

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

### Backend

- **Runtime:** Node.js 20+
- **Framework:** Express.js
- **API Layer:** tRPC (end-to-end type safety with frontend)
- **Database ORM:** Prisma
- **Caching/Rate Limiting:** Redis
- **Data Ingestion:** Reddit API (PRAW/custom HTTP client), Twitter API (via twitterapi.io)
- **Scraping Backup:** Playwright (when APIs rate-limited/unavailable)
- **AI Processing:** Claude Sonnet 4 API (extract structured data from posts)
- **Optional:** FastAPI + Python microservice (heavy NLP/data processing if needed)

### Frontend

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **UI Library:** React.js
- **Styling:** Tailwind CSS
- **Components:** Radix UI + Shadcn/ui
- **Package Manager:** Yarn

### Infrastructure

- **Database:** PostgreSQL via Supabase (free tier: 500MB, upgrade to Pro: 8GB @ $25/month)
- **Auth:** Supabase Auth
- **Backend Hosting:** Railway (Express + tRPC + Redis + Playwright)
- **Frontend Hosting:** Vercel
- **Containerization:** Not present initially, Docker added later for production

### Architecture Notes

- **Primary ingestion:** Reddit API + Twitter API (twitterapi.io proxy)
- **Backup ingestion:** Playwright scraping (fallback when API limits exceeded)
- **Type safety:** tRPC ensures frontend/backend contract enforcement
- **Supabase benefits:** PostgreSQL + Auth + Storage + Realtime in single platform
- **Railway deployment:** Single service for Node.js backend, Redis, and Playwright dependencies

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

**Extraction Model:** Claude Sonnet 4 (primary), consider cheaper alternatives like GLM-4.5 (https://docs.z.ai/scenario-example/develop-tools/claude) for cost optimization if volume scales

---

## Monetization Strategy

### Overview

WhichGLP's monetization approach prioritizes ethical revenue streams that align with the core mission of helping users make informed decisions about GLP-1 medications. As a solopreneur project, all revenue models are designed for automation with minimal ongoing operational overhead.

### Revenue Model Rankings

**Ranked by ROI for solopreneur implementation:**

#### Rank 1: Freemium Personalized Predictions ⭐⭐⭐⭐⭐

**Model:** Free basic features, premium subscription for advanced insights

**Free Tier Includes:**
- Basic drug comparison tables
- General statistics and aggregated outcomes
- Browse community reviews
- Access to educational content

**Premium Tier ($14.99/month or $99/year):**
- Detailed cohort analysis: "Based on 500+ users with your profile (male, 28, 200lbs, NYC, Aetna insurance)..."
- Weight loss trajectory predictions with confidence intervals
- Cost breakdown by insurance provider and pharmacy
- Side effect probability calculator personalized to demographics
- Monthly outcome reports as you track your journey
- Unlimited saved drug comparisons
- Early access to new features

**Solopreneur Advantages:**
- Fully automated - no customer service required
- 95%+ profit margins (server costs only)
- Scales infinitely without linear cost increases
- Aligns perfectly with core value proposition
- Sticky revenue (monthly recurring)

**Implementation Complexity:** Medium-High
- Requires polished premium features
- Payment integration (Stripe)
- User authentication system
- Premium content access controls

**Revenue Potential:**
- Target: 10,000 monthly active users
- Conversion rate: 2-5% (industry standard for freemium SaaS)
- Monthly revenue: 10,000 × 3% × $14.99 = **$4,497/month**
- Annual revenue: **~$54,000/year**

**Timeline:** 3-6 months to launch premium tier

**Priority:** PRIMARY revenue model - build this first

---

#### Rank 2: Affiliate Partnerships with Telehealth Providers ⭐⭐⭐⭐⭐

**Model:** Earn commissions by referring users to vetted telehealth providers

**Partner Examples:**
- **Hims** - $199-299/month GLP-1 programs
- **Ro** - $145-299/month subscriptions
- **Henry Meds** - $297/month compounded options
- **Calibrate** - $135/month with coaching
- **Sesame** - Pay-per-visit model

**Commission Structure:**
- Typical: 20-40% of first 3-6 months of patient subscriptions
- Average commission per referral: $150-400
- Cookie duration: 30-90 days

**Implementation:**
- "Find a Provider" page with curated telehealth options
- Pre-filled intake forms with drug preferences from user's comparison searches
- Transparent affiliate disclosure: "We may earn a commission if you sign up through our links"
- Track which providers users actually recommend in Reddit/Twitter data

**Solopreneur Advantages:**
- Zero operational overhead
- Passive income once implemented
- No inventory, fulfillment, or customer service
- Fast to implement (2-4 weeks)
- Helps users solve "where do I actually get this drug?" problem

**Ethical Safeguards:**
- Only partner with legitimate, licensed telehealth providers
- Clear disclosure of affiliate relationships
- User reviews of providers (from Reddit data) visible alongside recommendations
- Never hide non-affiliate options

**Revenue Potential:**
- Target: 100 referrals/month (1% of 10K MAU)
- Average commission: $200
- Monthly revenue: 100 × $200 = **$20,000/month**
- Annual revenue: **~$240,000/year**

**Note:** This is optimistic; realistic early-stage estimate is $2,000-5,000/month growing to $10,000-20,000/month at scale

**Timeline:** 2-4 weeks to set up partnerships and integration

**Priority:** QUICK WIN - implement immediately after MVP launch

---

#### Rank 3: Insurance Appeal Templates & Tools ⭐⭐⭐⭐

**Model:** Premium tier includes tools to fight insurance denials

**Problem Statement:**
- 60-64% of patients discontinue GLP-1s due to cost/loss of insurance coverage (Goldman Sachs)
- Insurance denials are common despite FDA approval for obesity
- Successful appeals exist but require documentation and persistence

**Premium Features (Included in $14.99/mo or $29 one-time):**
- **Appeal letter templates** by insurance provider (Aetna, UnitedHealthcare, BCBS, Cigna, etc.)
- **Medical necessity documentation guidance** - what your doctor needs to include
- **Peer-reviewed study citations** to attach to appeals (efficacy, cardiovascular benefits, diabetes prevention)
- **State-specific insurance regulations** and patient rights
- **Appeal status tracker** - organize your appeal process
- **Success story database** - anonymized successful appeals from Reddit with strategies used

**Data Source:**
- Extract successful appeal stories from Reddit using AI
- Example: "I got Wegovy covered after 2 appeals - here's what worked"
- Create templates based on patterns in successful appeals

**Solopreneur Advantages:**
- Create template library once, sell infinitely
- Minimal updates needed (quarterly as policies change)
- High perceived value relative to low production cost
- Solves major pain point = high conversion rate
- No ongoing customer support needed (templates are self-service)

**Ethical Value:**
- Directly helps people afford necessary medication
- Democratizes knowledge that wealthy patients get from expensive advocates
- Reduces discontinuation rate = better health outcomes

**Legal Considerations:**
- Include disclaimer: "Not legal advice, consult with your doctor"
- Review templates with healthcare compliance consultant ($500-1000 one-time)
- Update quarterly as insurance policies change

**Revenue Potential:**
- Embedded in premium tier: contributes to overall subscription value
- Standalone option: 200 purchases/month × $29 = $5,800/month
- Higher value: increases premium tier conversion rate by 1-2%

**Timeline:** 6-8 weeks to create comprehensive template library

**Priority:** PHASE 2 - add after core product is stable and premium tier is launched

---

#### Rank 4: B2B Data Licensing to Healthcare Companies ⭐⭐⭐⭐

**Model:** Sell aggregated, anonymized insights to healthcare organizations

**Potential Customers:**
- **Insurance companies** - Actuarial modeling for coverage decisions
- **Pharmaceutical companies** - Post-market surveillance, competitive intelligence
- **Healthcare research firms** - Market trend analysis
- **Hedge funds** - Investment thesis validation for pharma stocks
- **Consulting firms** - Healthcare strategy practices

**Product Offerings:**

**Quarterly Market Reports ($5,000-15,000):**
- Drug adoption trends by region and demographics
- Side effect prevalence rates vs clinical trial data
- Real-world discontinuation reasons (cost, side effects, efficacy)
- Cost burden analysis by insurance type
- Geographic pricing variations
- Emerging sentiment trends

**Custom Research Projects ($25,000-100,000):**
- Specific questions: "What % of Mounjaro users switch to Zepbound and why?"
- Demographic deep-dives
- Competitive landscape analysis
- Insurance coverage impact studies

**API Access (Enterprise Tier: $50,000+/year):**
- Real-time aggregated statistics API
- Query interface for custom analyses
- No PII, fully anonymized, aggregated only

**Ethical Safeguards:**
- **No raw data sales** - only aggregated insights (minimum 100+ users per data point)
- **No PII** - all data fully anonymized before analysis
- **IRB-style review** - internal ethics review for each customer/use case
- **Deny harmful use cases** - no selling to pharma for price manipulation, no predatory marketing uses
- **Transparency** - publish annual transparency report on data usage

**Compliance Requirements:**
- Legal review of data licensing agreements
- HIPAA compliance review (likely not applicable but verify)
- Terms of Service allowing aggregated data licensing (disclosed to users)

**Solopreneur Advantages:**
- High revenue per customer ($10K-50K per engagement)
- Quarterly cadence = manageable workload
- Automated report generation (Python scripts + Claude for analysis)
- Prestigious clients validate dataset quality
- Minimal ongoing support needed

**Challenges:**
- Long sales cycles (6-12 months from pitch to contract)
- Requires significant dataset size (target: 100K+ data points)
- Legal/compliance overhead
- Need credibility signals (whitepapers, published research)

**Revenue Potential:**
- Early stage: 2-4 customers × $10,000/quarter = $80,000-160,000/year
- Mature: 10-15 customers × $25,000/quarter = $250,000-375,000/year

**Timeline:** 6-12 months (need larger dataset first, build credibility)

**Priority:** PHASE 3 - pursue once 100K+ data points achieved and consumer product is successful

---

#### Rank 5: Pharmacy Price Comparison with Referral Fees ⭐⭐⭐

**Model:** GoodRx-style price comparison with affiliate revenue from pharmacies

**Feature Implementation:**
- "Where to buy Ozempic in [city]" → interactive map with real-time pricing
- Integration with GoodRx API, Blink Health, Cost Plus Drugs, SingleCare
- Show retail price vs discount card price vs insurance copay estimates
- User reviews of pharmacy experience (extracted from Reddit)

**Revenue Sources:**
- **Discount card usage fees:** $2-5 per prescription filled using WhichGLP discount code
- **Pharmacy referral fees:** Pharmacies pay for qualified traffic
- **Price alert premium feature:** Notify when drug price drops (premium tier)

**Differentiation from GoodRx:**
- **Community reviews of pharmacies** - "CVS on Main St was great, no judgment" vs "Walgreens pharmacist was rude about GLP-1s"
- **Drug-specific optimization** - Only show pharmacies that stock GLP-1s (many don't)
- **Insurance integration** - Compare discount card vs insurance copay

**Solopreneur Advantages:**
- API integrations available (GoodRx provides affiliate API)
- Fully automated after setup
- Clear user value (save money)
- Proven business model

**Challenges:**
- **Commoditized space** - GoodRx dominates with $100M+ revenue
- **Lower margins** - only $2-5 per transaction
- **Pharmacy partnerships** - requires business development effort
- **API costs** - GoodRx API may have usage fees

**Revenue Potential:**
- 500 pharmacy price checks/month
- 20% conversion to discount card usage
- 100 transactions × $3 average = **$300/month**
- At scale (10K MAU): 2,000 transactions × $3 = **$6,000/month**

**Timeline:** 4-6 weeks to implement API integrations

**Priority:** OPTIONAL - only pursue if freemium premium tier plateaus or as complementary feature

---

### Monetization Roadmap

**Phase 1 (Months 1-6): Foundation**
- Launch free tier with basic features
- Implement affiliate partnerships with telehealth providers (quick win)
- Build email list and user base
- Track conversion funnel metrics

**Phase 2 (Months 6-12): Premium Tier**
- Launch freemium premium tier ($14.99/month)
- Add insurance appeal templates and tools
- A/B test pricing and feature packaging
- Optimize conversion funnel

**Phase 3 (Months 12-24): Scale & Diversification**
- Expand dataset to 100K+ data points
- Begin B2B data licensing outreach
- Publish research whitepapers for credibility
- Consider pharmacy price comparison if premium plateaus

**Phase 4 (Months 24+): Enterprise & Partnerships**
- Formalize B2B data licensing program
- Explore white-label opportunities (license platform to clinics)
- International expansion (UK, Canada, Australia markets)
- Consider institutional partnerships (universities, research orgs)

---

### Revenue Projections

**Conservative Case (Year 1):**
- Freemium subscriptions: 50 paid users × $14.99 × 12 months = $8,994
- Telehealth affiliates: 20 referrals/month × $150 × 12 months = $36,000
- **Total Year 1: ~$45,000**

**Base Case (Year 2):**
- Freemium subscriptions: 300 paid users × $14.99 × 12 months = $53,964
- Telehealth affiliates: 100 referrals/month × $200 × 12 months = $240,000
- Insurance appeal standalone: 50 purchases/month × $29 × 12 months = $17,400
- **Total Year 2: ~$311,000**

**Optimistic Case (Year 3):**
- Freemium subscriptions: 1,000 paid users × $14.99 × 12 months = $179,880
- Telehealth affiliates: 300 referrals/month × $200 × 12 months = $720,000
- B2B data licensing: 4 customers × $10,000 × 4 quarters = $160,000
- **Total Year 3: ~$1,060,000**

---

### Ethical Principles

All monetization strategies adhere to these principles:

1. **User-First:** Never compromise data accuracy or hide information for revenue
2. **Transparency:** Clearly disclose affiliate relationships and sponsored content
3. **Privacy:** Never sell individual user data or PII
4. **Medical Ethics:** No partnerships with unethical providers or predatory lenders
5. **Accessibility:** Core functionality remains free for users who can't afford premium
6. **Truth in Advertising:** No false claims, no manipulation, no dark patterns
7. **Harm Reduction:** Actively prevent misuse of platform (e.g., promoting off-label use in populations without medical need)

---

## Root of this monorepo

This monorepo is rooted at this file's enclosing directory. That is, this file is (root)/AGENTS.md.

All git operations are to be run from this root directory.

All Python dependencies are to be installed from this root directory (with its venv activated), and all dependencies are to be listed in requirements.txt in this root directory via `$ pip3 freeze > requirements.txt`.

## Development Process

- Always consult the documentation, which you can fetch and follow, to make sure you understand how to use the libraries and tools available.
- If in doubt, conduct web searches to find additional relevant information. Fetch documentation and review it to ensure you understand how to use libraries and tools correctly.
- Work in this repo/directory (and its subdirectories) only. Never touch any files outside this repo/directory/subdirectories unless explicitly instructed to do so.
- It is your responsibility to manage the environment (using 'uv' if Python), prepare it for working, updating dependencies, and installing any new dependencies you may need. E.g., whenever you need to install a new Python package, you should install it in the virtual environment using pip (`$ pip3 install --upgrade <package_name>`) and then update the requirements.txt file accordingly using `$ pip3 freeze > requirements.txt`.
- Always test your changes before moving on to the next checkpoint/milestone. Make sure everything works as expected.

## Coding

Style
- If Python code, then use Python 3 and follow PEP8 style guidelines.
- Prioritise readability - make code easy to read and understand by using small functions, avoiding unnecessary complexity (including sophisticated safety mechanisms, typing, complex patterns, etc. ... when they are not strictly necessary).
- Add type hints whenever possible. Make sure the type hints are correct; watch out especially for complex types (e.g., lists of dictionaries, optional types, etc.).
- Use linters/formatters (e.g., black, flake8 for Python; eslint, prettier for JavaScript/TypeScript) to ensure consistent code style.
- Write unit tests and integration tests for critical functions and components. Use testing frameworks like pytest (Python), or Jest or React Testing Library (JavaScript/TypeScript).
- Follow best practices for error handling and logging. Use try-except blocks in Python, and proper error handling in JavaScript/TypeScript (e.g., Promises with .catch). Use descriptive error messages and error class names.
- Use consistent naming conventions for variables, functions, classes, and modules. Prefer descriptive names over abbreviations.
- Write modular code - break down large functions into smaller, reusable functions.
- Concise but clear explanatory comments to all code paths. The code you generated is being read by humans to learn and understand how the program works, so make it easy for them to follow. Add comments to every function, every if and else block, everywhere where commentary can help the reader understand how the code works.
- Always prefer clarity over brevity.
- Use docstrings, multiline comments, etc. (as the convention may be with the particular framework/library/language) to document all functions, classes, and modules. Include descriptions of parameters, return values, and any exceptions raised.
- Include links to any online docs or references you used to learn how to use a library, tool, or API, if applicable.
- Remove any unused imports, variables, functions, or code blocks.
- Avoid hardcoding values; use constants or configuration files instead.

## Living Documentation (the file ./AGENTS_APPENDLOG.md)

- That document (AGENTS_APPENDLOG.md) serves as the secondary instruction for you, after this primary AGENTS.md.
- Append to that document only. Do not remove or modify existing content, even if it is incorrect or outdated. That document is meant to be an append-only log.
- Keep notes there about your development process, decisions made, the current architecture of the project.
- Whenever you make code changes, remember to append your proposed changes to that file (append-only; don't delete its existing content), and then append to that file again to state that you've completed the changes when you've completed the changes
- That document is very long and won't fit into your context window. No worries: you don't have to read all of it. Please just, say, read the last 100 lines of it to know generally what's in it, and then append, since it's an append-only doc.