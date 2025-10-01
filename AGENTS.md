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
   - **Reddit Presence:** r/Mounjaro (85K members), r/zepbound (62K members), r/tirzepatide (28K members)

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
6. **r/tirzepatide** (28K members) - Generic tirzepatide discussions

**Tier 2 - General GLP-1 Discussions:**
7. **r/GLP1Agonists** (35K members) - Cross-drug comparisons, general questions
8. **r/WegovyWeightLoss** (18K members) - Success stories, tips
9. **r/liraglutide** (12K members) - Older drug, generic now available

**Tier 3 - Broader Weight Loss Communities:**
10. **r/loseit** (4.2M members) - General weight loss, GLP-1 discussions in comments
11. **r/obesity** (120K members) - Medical obesity discussions
12. **r/SuperMorbidlyObese** (90K members) - Higher BMI users, often discuss GLP-1s
13. **r/progresspics** (2.8M members) - Before/after photos, GLP-1 mentions in titles/comments

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

## More Info On This Project

See ./README.md for tech stack and more info.

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
- Write modular code - break down large functions into smaller, reusable functions.
- Concise but clear explanatory comments to all code paths. The code you generated is being read by humans to learn and understand how the program works, so make it easy for them to follow. Add comments to every function, every if and else block, everywhere where commentary can help the reader understand how the code works.
- Always prefer clarity over brevity.
- Use docstrings, multiline comments, etc. (as the convention may be with the particular framework/library/language) to document all functions, classes, and modules. Include descriptions of parameters, return values, and any exceptions raised.


## Living Documentation (the file ./AGENTS_APPENDLOG.md)

- That document (AGENTS_APPENDLOG.md) serves as the secondary instruction for you, after this primary AGENTS.md.
- Append to that document only. Do not remove or modify existing content, even if it is incorrect or outdated. That document is meant to be an append-only log.
- Keep notes there about your development process, decisions made, the current architecture of the project.
- Whenever you make code changes, remember to append your proposed changes to that file (append-only; don't delete its existing content), and then append to that file again to state that you've completed the changes when you've completed the changes