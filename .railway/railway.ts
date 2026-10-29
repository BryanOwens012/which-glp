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
  database,
  defineRailway,
  fn,
  github,
  image,
  preserve,
  project,
  service,
  volume,
  type DatabaseNode,
  type ServiceNetworking,
  type SharedVariableRef,
  type VariableValue,
} from "railway/iac";

const REPO = "BryanOwens012/which-glp";
/** Production deploys track this branch. `github()` defaults to "main", so keep this explicit. */
const BRANCH = "develop";
const US_EAST = "us-east4-eqdc4a";
const US_WEST = "us-west2";

const FUNCTION_IMAGE = "ghcr.io/railwayapp/function-bun:1.4.4";
/** Railway patches the function image daily between 02:00 and 06:00 UTC. */
const FUNCTION_AUTO_UPDATES = {
  type: "patch",
  schedule: [0, 1, 2, 3, 4, 5, 6].map((day) => ({ day, startHour: 2, endHour: 6 })),
} as const;
const REDIS_IMAGE = "redis:8.2.2";

// Restart policy is deliberately not declared on long-running services: Railway's
// default is ON_FAILURE with 10 retries, and it reads that default back as null, so
// declaring it keeps every plan dirty without changing behavior. Functions declare
// NEVER because that is not the default.

/** Per-container CPU and memory caps as Railway currently holds them (memory in decimal bytes). */
const buildLimits = (cpu: number, memoryGb: number) => ({
  limitOverride: { containers: { cpu, memoryBytes: memoryGb * 1_000_000_000 } },
});

/**
 * Seconds Railway waits between SIGTERM and SIGKILL on redeploy. Railway's default
 * is 0, which kills in-flight requests and skips every shutdown handler. Longer
 * than the API's SHUTDOWN_TIMEOUT_MS (10 s) so its graceful shutdown can finish;
 * uvicorn drains in-flight requests on SIGTERM by default.
 */
const DRAINING_SECONDS = 15;

/*
 * Each service declares only the variables its own code reads; `npm run check`
 * fails on a declared variable that the service's code never mentions. Values are
 * managed on Railway and preserved as-is.
 */
const supabaseApi = ["SUPABASE_SECRET_KEY", "SUPABASE_URL"] as const;
const redditApi = ["REDDIT_API_APP_ID", "REDDIT_API_APP_NAME", "REDDIT_API_APP_SECRET"] as const;

/**
 * Every shared variable defined on the production environment, by name. A service
 * variable with one of these names must be a `${{shared.NAME}}` reference, never
 * its own copy: `buildEnv` makes it one, and `npm run check` fails on any other
 * form. This is a hand-kept mirror of Railway's shared variables (dashboard:
 * environment Settings > Shared Variables): `check` cannot see a shared variable
 * missing from it, so add the name here whenever one is created in Railway. The
 * shared variables themselves are set in Railway and are not managed by this file.
 */
export const SHARED_VARIABLES: ReadonlySet<string> = new Set([
  "ANTHROPIC_API_KEY",
  "DOPPLER_CONFIG",
  "DOPPLER_ENVIRONMENT",
  "DOPPLER_PROJECT",
  "DOPPLER_TOKEN",
  "INTERNAL_API_KEY",
  "OPENROUTER_API_KEY",
  "POSTHOG_API_KEY",
  "POSTHOG_HOST",
  "REDDIT_API_APP_ID",
  "REDDIT_API_APP_NAME",
  "REDDIT_API_APP_SECRET",
  "SUPABASE_DB_PASSWORD",
  "SUPABASE_PUBLISHABLE_KEY",
  "SUPABASE_SECRET_KEY",
  "SUPABASE_URL",
]);

/**
 * Every backend service gets the environment's DOPPLER_TOKEN, a shared reference like
 * any other: a service token, bound to one project and config, so none is sent. Each
 * service loads its own enumerated secrets with it at boot; see
 * apps/api/src/lib/doppler-secrets.ts.
 */
const DOPPLER_TOKEN_VARIABLE = "DOPPLER_TOKEN";

type ServiceEnv = Record<string, string | VariableValue>;

/** A service's variables (shared ones as references, the rest preserved), plus the Doppler token. */
const buildEnv = (shared: SharedVariableRef, names: readonly string[]): ServiceEnv =>
  Object.fromEntries(
    [...new Set([...names, DOPPLER_TOKEN_VARIABLE])].map((name) => [
      name,
      SHARED_VARIABLES.has(name) ? shared[name] : preserve(),
    ]),
  );

/**
 * A Railway Function's source: the shared Doppler loader (functions/_doppler-secrets.ts)
 * followed by the function's own file, so every function carries one copy of it.
 */
export const buildFunctionSource = (file: string): Buffer =>
  Buffer.concat([
    readFileSync(join(import.meta.dirname, "functions", "_doppler-secrets.ts")),
    Buffer.from("\n"),
    readFileSync(join(import.meta.dirname, "functions", file)),
  ]);

/** A Railway Function's code ships base64-encoded in its start command. */
const encodeFunction = (file: string): string => `./run.sh ${buildFunctionSource(file).toString("base64")}`;

const buildUvicornStart = (dir: string): string =>
  `cd apps/${dir} && uvicorn api:app --host 0.0.0.0 --port $PORT`;

/**
 * Railway keeps a private-network hostname (<endpoint>.railway.internal) and a
 * generated public domain per service. Both are live state the plan diffs, so they
 * are declared here rather than left to be cleared.
 */
const buildNetworking = (privateEndpoint: string, serviceDomain?: string): ServiceNetworking => ({
  privateNetworkEndpoint: privateEndpoint,
  ...(serviceDomain ? { serviceDomains: { [serviceDomain]: { port: 8080 } } } : {}),
});

type PythonServiceOptions = {
  /** Directory under apps/; also scopes the watch pattern so unrelated commits skip the deploy. */
  dir: string;
  start: string;
  /** Seconds Railway waits for /health before failing the deploy. */
  healthcheckTimeout: number;
  cpu: number;
  /** Hostname on the private network, without the .railway.internal suffix. */
  privateEndpoint: string;
  /** Railway-generated public domain. */
  serviceDomain: string;
  env: ServiceEnv;
};

/** The Python services build from the monorepo root (no root directory) with Railpack. */
const definePythonService = (
  name: string,
  { dir, start, healthcheckTimeout, cpu, privateEndpoint, serviceDomain, env }: PythonServiceOptions,
) =>
  service(name, {
    source: github(REPO, { branch: BRANCH }),
    build: { builder: "RAILPACK", watchPatterns: [`/apps/${dir}/**`] },
    start,
    healthcheck: "/health",
    healthcheckTimeout,
    deploy: { ...buildLimits(cpu, 8), drainingSeconds: DRAINING_SECONDS },
    replicas: { [US_EAST]: 1 },
    networking: buildNetworking(privateEndpoint, serviceDomain),
    env,
  });

type CronFunctionOptions = {
  /** File under ./functions whose contents become the function body. */
  file: string;
  /** Standard 5-field cron expression, evaluated in UTC. */
  schedule: string;
  privateEndpoint: string;
  env: ServiceEnv;
};

const defineCronFunction = (
  name: string,
  { file, schedule, privateEndpoint, env }: CronFunctionOptions,
) =>
  fn(name, {
    source: image(FUNCTION_IMAGE, { autoUpdates: FUNCTION_AUTO_UPDATES }),
    start: encodeFunction(file),
    deploy: { cronSchedule: schedule, restartPolicyType: "NEVER", ...buildLimits(4, 4) },
    replicas: { [US_EAST]: 1 },
    networking: buildNetworking(privateEndpoint),
    env,
  });

/**
 * Railway tracks Redis as a database resource: its image, start command, and
 * limits live on the node, while its variables, TCP proxy, and volume mount are
 * managed by the database product and are absent from the graph. The redis()
 * helper assumes railwayapp/redis on /bitnami, so the engine-level helper is used
 * with this instance's real image and mount path.
 */
const defineRedisDatabase = (name: string): DatabaseNode => {
  const node = database(name, "redis", {
    image: REDIS_IMAGE,
    output: "REDIS_URL",
    defaultMountPath: "/data",
    region: US_EAST,
  });
  return {
    ...node,
    deploy: {
      ...node.deploy,
      startCommand:
        '/bin/sh -c "rm -rf $RAILWAY_VOLUME_MOUNT_PATH/lost+found/ && exec docker-entrypoint.sh redis-server --requirepass $REDIS_PASSWORD --save 60 1 --dir $RAILWAY_VOLUME_MOUNT_PATH"',
      ...buildLimits(4, 8),
    },
  };
};

export default defineRailway((ctx) => {
  const env = (names: readonly string[]) => buildEnv(ctx.shared, names);

  // Node.js tRPC API. Serves api.whichglp.com from two regions.
  const api = service("API", {
    source: github(REPO, { branch: BRANCH, rootDirectory: "apps/api" }),
    build: { builder: "NIXPACKS", watchPatterns: ["/apps/api/**"] },
    start: "npm start",
    deploy: { ...buildLimits(8, 8), drainingSeconds: DRAINING_SECONDS },
    replicas: { [US_EAST]: 1, [US_WEST]: 1 },
    domains: [{ domain: "api.whichglp.com", port: 8080 }],
    networking: buildNetworking("which-glp", "backend-production-71c7.up.railway.app"),
    env: env(["INTERNAL_API_KEY", "POSTHOG_API_KEY", "POSTHOG_HOST", "REC_ENGINE_URL", "REDIS_URL", ...supabaseApi]),
  });

  const postIngestion = definePythonService("Post-Ingestion", {
    dir: "post-ingestion",
    start: buildUvicornStart("post-ingestion"),
    healthcheckTimeout: 100,
    cpu: 4,
    privateEndpoint: "post-ingestion",
    serviceDomain: "whichglp-post-ingestion.up.railway.app",
    env: env(["INTERNAL_API_KEY", "PYTHONUNBUFFERED", ...redditApi, ...supabaseApi]),
  });

  const postExtraction = definePythonService("Post-Extraction", {
    dir: "post-extraction",
    start: buildUvicornStart("post-extraction"),
    healthcheckTimeout: 100,
    cpu: 8,
    privateEndpoint: "post-extraction",
    serviceDomain: "whichglp-post-extraction.up.railway.app",
    env: env(["INTERNAL_API_KEY", "OPENROUTER_API_KEY", ...supabaseApi]),
  });

  const userExtraction = definePythonService("User-Extraction", {
    dir: "user-extraction",
    start: buildUvicornStart("user-extraction"),
    healthcheckTimeout: 100,
    cpu: 8,
    privateEndpoint: "which-glp-4741320e",
    serviceDomain: "whichglp-user-extraction.up.railway.app",
    env: env(["INTERNAL_API_KEY", "OPENROUTER_API_KEY", ...redditApi, ...supabaseApi]),
  });

  // FastAPI recommendation engine. The 300-second healthcheck window carries over from its railway.json.
  const recEngine = definePythonService("Rec-Engine", {
    dir: "rec-engine",
    start: "cd apps/rec-engine && python3 api.py",
    healthcheckTimeout: 300,
    cpu: 8,
    privateEndpoint: "ml",
    serviceDomain: "whichglp-rec-engine.up.railway.app",
    env: env(["INTERNAL_API_KEY", ...supabaseApi]),
  });

  // Redis cache used by the API. The volume is declared alongside so Railway keeps
  // the existing resource; the database product owns the mount.
  const redisVolume = volume("redis-volume", {
    region: US_EAST,
    sizeMB: 5000,
    allowOnlineResize: true,
    alerts: { usage: { "80": {}, "95": {}, "100": {} } },
  });
  const redisCache = defineRedisDatabase("Redis");

  // Daily pipeline triggers, implemented as Railway Functions (Bun). Each one POSTs
  // to its service's internal endpoint; see ./functions for the code.
  const postIngestionCron = defineCronFunction("Post-Ingestion-Cron", {
    file: "post-ingestion-cron.ts",
    schedule: "0 0 * * *",
    privateEndpoint: "post-ingestion-cron",
    env: env(["INTERNAL_API_KEY", "POST_INGESTION_URL"]),
  });

  const postExtractionCron = defineCronFunction("Post-Extraction-Cron", {
    file: "post-extraction-cron.ts",
    schedule: "0 6 * * *",
    privateEndpoint: "post-extraction-cron",
    env: env(["INTERNAL_API_KEY", "POST_EXTRACTION_URL"]),
  });

  const userExtractionCron = defineCronFunction("User-Extraction-Cron", {
    file: "user-extraction-cron.ts",
    schedule: "0 17 * * *",
    privateEndpoint: "user-extraction-cron",
    env: env(["INTERNAL_API_KEY", "USER_EXTRACTION_URL"]),
  });

  // Refreshes the denormalized materialized view straight against Postgres.
  const viewRefresherCron = defineCronFunction("View-Refresher-Cron", {
    file: "view-refresher-cron.ts",
    schedule: "0 18 * * *",
    privateEndpoint: "function-bun",
    env: env(["REDIS_URL", "SUPABASE_DB_PASSWORD", "SUPABASE_URL"]),
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
