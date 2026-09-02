/**
 * Railway Infrastructure as Code for the WhichGLP project.
 *
 * This file is the single source of truth for the `production` environment on
 * Railway: every service, its source, build and deploy settings, custom domain,
 * TCP proxy, volume, and the NAMES of its variables. Variable values stay on
 * Railway (`preserve()`), so nothing secret is committed here.
 *
 * Workflow (Railway CLI >= 5.42.1, run from a directory linked to the project):
 *
 *   railway config plan    # read-only diff of this file against the live environment
 *   railway config apply   # apply, after reviewing the plan
 *
 * Rules that keep this safe:
 *   - Omitting a service, variable, domain, proxy, or volume here DELETES it on
 *     apply. Add a resource here before creating it in the dashboard, and never
 *     remove one here unless you mean to destroy it.
 *   - Railway Function (cron) source lives in ./functions/*.ts and is encoded into
 *     each function's start command below. Edit the .ts file, then plan and apply.
 *   - `railway config pull` overwrites this file from live state. Run it on a scratch
 *     branch to see drift, fold the differences back in by hand, then discard the pull.
 *   - Cron schedules are UTC.
 *
 * Reference: https://docs.railway.com/infrastructure-as-code/reference
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  defineRailway,
  fn,
  github,
  image,
  preserve,
  project,
  service,
  volume,
  type VariableValue,
} from "railway/iac";

const REPO = "BryanOwens012/which-glp";
/** Production deploys track this branch. `github()` defaults to "main", so keep this explicit. */
const BRANCH = "develop";
const US_EAST = "us-east4-eqdc4a";
const US_WEST = "us-west2";

const FUNCTION_IMAGE = "ghcr.io/railwayapp/function-bun:1.3.0";
const REDIS_IMAGE = "redis:8.2.2";

const ON_FAILURE_RESTART = {
  restartPolicyType: "ON_FAILURE",
  restartPolicyMaxRetries: 10,
} as const;

/** Per-container CPU and memory caps as Railway currently holds them (memory in decimal bytes). */
const buildLimits = (cpu: number, memoryGb: number) => ({
  limitOverride: { containers: { cpu, memoryBytes: memoryGb * 1_000_000_000 } },
});

/** Variables every service carries. Values are managed on Railway and preserved as-is. */
const sharedSecrets = [
  "ANTHROPIC_API_KEY",
  "INTERNAL_API_KEY",
  "POSTHOG_API_KEY",
  "POSTHOG_HOST",
  "REDDIT_API_APP_ID",
  "REDDIT_API_APP_NAME",
  "REDDIT_API_APP_SECRET",
  "REDIS_URL",
  "SUPABASE_ANON_KEY",
  "SUPABASE_DB_PASSWORD",
  "SUPABASE_SERVICE_KEY",
  "SUPABASE_URL",
] as const;

/** Extra variables on the LLM ingestion/extraction services and their cron triggers. */
const extractionSecrets = ["GLM_API_KEY", "GLM_API_URL", "GLM_MODEL", "OPENAI_API_KEY"] as const;

const preserveAll = (names: readonly string[]): Record<string, VariableValue> =>
  Object.fromEntries(names.map((name) => [name, preserve()]));

/** A Railway Function's code ships base64-encoded in its start command. */
const encodeFunction = (file: string): string => {
  const source = readFileSync(join(import.meta.dirname, "functions", file));
  return `./run.sh ${source.toString("base64")}`;
};

const buildUvicornStart = (dir: string): string =>
  `cd apps/${dir} && uvicorn api:app --host 0.0.0.0 --port $PORT`;

type PythonServiceOptions = {
  /** Directory under apps/; also scopes the watch pattern so unrelated commits skip the deploy. */
  dir: string;
  start: string;
  /** Seconds Railway waits for /health before failing the deploy. */
  healthcheckTimeout: number;
  cpu: number;
  env: readonly string[];
};

/** The Python services build from the monorepo root (no root directory) with Railpack. */
const definePythonService = (
  name: string,
  { dir, start, healthcheckTimeout, cpu, env }: PythonServiceOptions,
) =>
  service(name, {
    source: github(REPO, { branch: BRANCH }),
    build: { builder: "RAILPACK", watchPatterns: [`/apps/${dir}/**`] },
    start,
    healthcheck: "/health",
    healthcheckTimeout,
    deploy: { ...ON_FAILURE_RESTART, ...buildLimits(cpu, 8) },
    replicas: { [US_EAST]: 1 },
    env: preserveAll(env),
  });

type CronFunctionOptions = {
  /** File under ./functions whose contents become the function body. */
  file: string;
  /** Standard 5-field cron expression, evaluated in UTC. */
  schedule: string;
  env: readonly string[];
};

const defineCronFunction = (name: string, { file, schedule, env }: CronFunctionOptions) =>
  fn(name, {
    source: image(FUNCTION_IMAGE),
    start: encodeFunction(file),
    deploy: { cronSchedule: schedule, restartPolicyType: "NEVER", ...buildLimits(4, 4) },
    replicas: { [US_EAST]: 1 },
    env: preserveAll(env),
  });

export default defineRailway(() => {
  // Node.js tRPC API. Serves api.whichglp.com from two regions.
  const api = service("API", {
    source: github(REPO, { branch: BRANCH, rootDirectory: "apps/api" }),
    build: { builder: "NIXPACKS", watchPatterns: ["/apps/api/**"] },
    start: "npm start",
    deploy: { ...ON_FAILURE_RESTART, ...buildLimits(8, 8) },
    replicas: { [US_EAST]: 1, [US_WEST]: 1 },
    domains: [{ domain: "api.whichglp.com", port: 8080 }],
    env: preserveAll([...sharedSecrets, "REC_ENGINE_URL"]),
  });

  const postIngestion = definePythonService("Post-Ingestion", {
    dir: "post-ingestion",
    start: buildUvicornStart("post-ingestion"),
    healthcheckTimeout: 100,
    cpu: 4,
    env: [...sharedSecrets, ...extractionSecrets, "PYTHONUNBUFFERED"],
  });

  const postExtraction = definePythonService("Post-Extraction", {
    dir: "post-extraction",
    start: buildUvicornStart("post-extraction"),
    healthcheckTimeout: 100,
    cpu: 8,
    env: [...sharedSecrets, ...extractionSecrets],
  });

  const userExtraction = definePythonService("User-Extraction", {
    dir: "user-extraction",
    start: buildUvicornStart("user-extraction"),
    healthcheckTimeout: 100,
    cpu: 8,
    env: [...sharedSecrets, ...extractionSecrets],
  });

  // FastAPI recommendation engine. The 300-second healthcheck window carries over from its railway.json.
  const recEngine = definePythonService("Rec-Engine", {
    dir: "rec-engine",
    start: "cd apps/rec-engine && python3 api.py",
    healthcheckTimeout: 300,
    cpu: 8,
    env: sharedSecrets,
  });

  // Redis cache used by the API. Declared as a plain image service rather than the
  // redis() helper because the helper assumes railwayapp/redis on /bitnami, while
  // this instance runs the official image with its data on /data.
  const redisVolume = volume("redis-volume", { region: US_EAST, sizeMB: 5000 });
  const redisCache = service("Redis", {
    source: image(REDIS_IMAGE),
    start:
      '/bin/sh -c "rm -rf $RAILWAY_VOLUME_MOUNT_PATH/lost+found/ && exec docker-entrypoint.sh redis-server --requirepass $REDIS_PASSWORD --save 60 1 --dir $RAILWAY_VOLUME_MOUNT_PATH"',
    deploy: { ...ON_FAILURE_RESTART, ...buildLimits(4, 8) },
    replicas: { [US_EAST]: 1 },
    tcp: [6379],
    volumeMounts: { "/data": redisVolume },
    env: preserveAll([
      "INTERNAL_API_KEY",
      "REDIS_PASSWORD",
      "REDIS_PUBLIC_URL",
      "REDIS_URL",
      "REDISHOST",
      "REDISPASSWORD",
      "REDISPORT",
      "REDISUSER",
    ]),
  });

  // Daily pipeline triggers, implemented as Railway Functions (Bun). Each one POSTs
  // to its service's internal endpoint; see ./functions for the code.
  const postIngestionCron = defineCronFunction("Post-Ingestion-Cron", {
    file: "post-ingestion-cron.ts",
    schedule: "0 0 * * *",
    env: [...sharedSecrets, ...extractionSecrets, "POST_INGESTION_URL"],
  });

  const postExtractionCron = defineCronFunction("Post-Extraction-Cron", {
    file: "post-extraction-cron.ts",
    schedule: "0 6 * * *",
    env: [...sharedSecrets, ...extractionSecrets, "POST_EXTRACTION_URL"],
  });

  const userExtractionCron = defineCronFunction("User-Extraction-Cron", {
    file: "user-extraction-cron.ts",
    schedule: "0 17 * * *",
    env: [...sharedSecrets, ...extractionSecrets, "USER_EXTRACTION_URL"],
  });

  // Refreshes the denormalized materialized view straight against Postgres.
  const viewRefresherCron = defineCronFunction("View-Refresher-Cron", {
    file: "view-refresher-cron.ts",
    schedule: "0 18 * * *",
    env: [...sharedSecrets, ...extractionSecrets],
  });

  return project("WhichGLP", {
    resources: [
      api,
      postIngestion,
      postExtraction,
      userExtraction,
      recEngine,
      redisCache,
      redisVolume,
      postIngestionCron,
      postExtractionCron,
      userExtractionCron,
      viewRefresherCron,
    ],
  });
});
