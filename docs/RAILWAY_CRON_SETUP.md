# Railway Cron Jobs

The data pipeline runs on four daily cron triggers. Each is a Railway Function (Bun runtime, image `ghcr.io/railwayapp/function-bun`) declared in [`.railway/railway.ts`](../.railway/railway.ts), with its source in [`.railway/functions/`](../.railway/functions/). The function's code is base64-encoded into the service's start command by `railway.ts`, so the repo, not the dashboard editor, is the source of truth.

## Schedule (UTC)

| Service | Source | Schedule | What it does |
|---|---|---|---|
| Post-Ingestion-Cron | `post-ingestion-cron.ts` | `0 0 * * *` | `POST /api/ingest` on Post-Ingestion (Tier 1 subreddits) |
| Post-Extraction-Cron | `post-extraction-cron.ts` | `0 6 * * *` | `POST /api/extract?limit=1000` on Post-Extraction |
| User-Extraction-Cron | `user-extraction-cron.ts` | `0 17 * * *` | `POST /api/analyze` on User-Extraction |
| View-Refresher-Cron | `view-refresher-cron.ts` | `0 18 * * *` | `REFRESH MATERIALIZED VIEW mv_experiences_denormalized` against Postgres, then deletes the `drugs:all-stats` Redis key |

The stagger gives each stage time to finish before the next one reads its output. Railway cron expressions are standard 5-field crontab syntax evaluated in UTC.

## How a trigger works

- The three service triggers read their target from `POST_INGESTION_URL`, `POST_EXTRACTION_URL`, or `USER_EXTRACTION_URL` (a bare hostname, prefixed with `https://`), falling back to the service's `.railway.internal` private domain.
- Requests carry `x-internal-api-key: $INTERNAL_API_KEY`; the services reject calls without it.
- A `409 Conflict` means the service is already running that job. The trigger logs it and exits; the next scheduled run tries again.
- Functions use `restartPolicyType: NEVER`, so a failed run is not retried until the next schedule.

## Changing a schedule or a function

1. Edit the schedule in `railway.ts` or the body in `.railway/functions/<name>.ts`.
2. From `.railway/`: `npm run typecheck && npm run check`.
3. `railway config plan`, review, then `railway config apply` (Bryan).

## Monitoring

```bash
# Logs for one trigger (service names are display names)
railway logs -s Post-Ingestion-Cron -p df649372-5b20-4e68-8ccd-31935edceade -e production

# Service status and health
curl https://whichglp-post-ingestion.up.railway.app/api/status
curl https://whichglp-post-ingestion.up.railway.app/health
```

## Manual trigger

Call the service endpoint directly with the internal key, for example:

```bash
curl -X POST "https://whichglp-post-extraction.up.railway.app/api/extract?limit=100" \
  -H "x-internal-api-key: $INTERNAL_API_KEY" -H "Content-Type: application/json" -d '{}'
```

## Troubleshooting

- **Trigger ran but nothing happened:** check the target `*_URL` variable and that `INTERNAL_API_KEY` matches the service's value.
- **Timeouts:** reduce the batch size in the function body (`limit`) or in the service, then plan and apply.
- **Health check failures:** verify the service is deployed and `/health` returns 200 before blaming the trigger.

## Cost

Reduce frequency by editing the schedule in `railway.ts` (for example `0 2 * * 0` for weekly) or reduce the per-run batch sizes in the function bodies.
