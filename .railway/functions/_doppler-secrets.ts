// Doppler secret loader for the cron functions. `railway.ts` prepends this file to
// each function's source when encoding it, so every function gets one copy; each
// function awaits loadDopplerSecrets with its own list of secret names inside its
// main, before its first secret read. Same behavior and log format as
// `apps/api/src/lib/doppler-secrets.ts` and
// `scripts/legacy-ingestion/shared/doppler_secrets.py`; keep the three in sync.
//
// Fetches only the enumerated names, one request each, with DOPPLER_TOKEN (a service
// token, bound to one project and config, so none is sent); writes pulled values into
// process.env for this run only; logs pulled and failed names with reasons, never a value.
// On Railway a missing or non-service token, or any failed name, throws: Railway holds
// no copy of Doppler's variables, so the run fails closed.

const DOPPLER_SECRET_URL = "https://api.doppler.com/v3/configs/config/secret";
// Variables Railway sets on every deployment; any one of them means the run is on Railway.
const RAILWAY_IDENTIFIERS = ["RAILWAY_ENVIRONMENT_NAME", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID"];
const DOPPLER_SECRET_NAME_PATTERN = /^[A-Z][A-Z0-9_]*$/;
const DOPPLER_REQUEST_TIMEOUT_MS = 5_000;
const DOPPLER_MAX_ATTEMPTS = 3; // 429 and 5xx responses and network errors are retried
const DOPPLER_RETRY_BASE_DELAY_MS = 250;
const DOPPLER_MAX_RETRY_AFTER_MS = 5_000; // a Retry-After header is honored up to this cap

async function loadDopplerSecrets(names: readonly string[]): Promise<void> {
  const token = process.env.DOPPLER_TOKEN;
  // Railway holds no copy of Doppler's variables, so there the load fails closed.
  const isOnRailway = RAILWAY_IDENTIFIERS.some((name) => Boolean(process.env[name]));
  if (!token) {
    if (isOnRailway) {
      throw new Error("[doppler] DOPPLER_TOKEN is not set; refusing to run without the Doppler variables");
    }
    console.info("[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (local .env applies)");
    return;
  }
  // We send no project or config, so only a service token, which is bound to one, can name what to read.
  if (!token.startsWith("dp.st.")) {
    if (isOnRailway) {
      throw new Error("[doppler] DOPPLER_TOKEN is not a service token (dp.st.); refusing to run without the Doppler variables");
    }
    console.warn("[doppler] DOPPLER_TOKEN is not a service token (dp.st.); skipping the Doppler load (local .env applies)");
    return;
  }

  const getRetryDelayMs = (attempt: number, retryAfter: string | null): number => {
    // An empty header would read as 0 seconds; treat it like a missing one.
    const seconds = retryAfter === null || retryAfter.trim() === '' ? Number.NaN : Number(retryAfter);
    if (Number.isFinite(seconds)) {
      return Math.min(Math.max(seconds * 1000, 0), DOPPLER_MAX_RETRY_AFTER_MS);
    }
    return DOPPLER_RETRY_BASE_DELAY_MS * 4 ** (attempt - 1) * (1 + Math.random() * 0.5);
  };

  const fetchSecret = async (name: string): Promise<{ name: string; value?: string; reason?: string }> => {
    const params = new URLSearchParams({ name });
    let lastReason = "error network";
    for (let attempt = 1; attempt <= DOPPLER_MAX_ATTEMPTS; attempt++) {
      let retryAfter: string | null = null;
      try {
        const response = await fetch(`${DOPPLER_SECRET_URL}?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
          signal: AbortSignal.timeout(DOPPLER_REQUEST_TIMEOUT_MS),
          redirect: "error", // never follow a redirect, so the token is only ever sent to Doppler
        });
        if (response.ok) {
          const body = (await response.json()) as { value?: { computed?: unknown } } | null;
          const value = body?.value?.computed;
          return typeof value === "string" && value !== "" ? { name, value } : { name, reason: "empty" };
        }
        if (response.status === 404) {
          return { name, reason: "not_found" };
        }
        lastReason = `error ${response.status}`;
        if (!(response.status === 429 || response.status >= 500)) {
          return { name, reason: lastReason };
        }
        retryAfter = response.headers.get("retry-after");
      } catch {
        lastReason = "error network";
      }
      if (attempt < DOPPLER_MAX_ATTEMPTS) {
        await new Promise((resolve) => setTimeout(resolve, getRetryDelayMs(attempt, retryAfter)));
      }
    }
    return { name, reason: lastReason };
  };

  const unique = [...new Set(names)].sort();
  const pulled: string[] = [];
  const failed: { name: string; reason: string }[] = [];
  const requested = unique.filter((name) => {
    if (DOPPLER_SECRET_NAME_PATTERN.test(name)) {
      return true;
    }
    failed.push({ name, reason: "invalid_name" });
    return false;
  });
  const outcomes = await Promise.all(requested.map(fetchSecret));
  // The token reads the whole Doppler config; nothing after the load needs it, so drop it.
  delete process.env.DOPPLER_TOKEN;
  for (const outcome of outcomes) {
    if (outcome.value !== undefined) {
      process.env[outcome.name] = outcome.value;
      pulled.push(outcome.name);
    } else {
      failed.push({ name: outcome.name, reason: outcome.reason ?? "error network" });
    }
  }
  failed.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0)); // plain string order, as in Python for ASCII names

  const line = `[doppler] pulled ${pulled.length} of ${pulled.length + failed.length} secrets, ${failed.length} failed; pulled=${JSON.stringify(pulled)} failed=${JSON.stringify(failed.map(({ name, reason }) => `${name} (${reason})`))}`;
  if (failed.length > 0) {
    console.warn(line);
    if (isOnRailway) {
      throw new Error(`[doppler] ${failed.length} variable(s) failed to load; refusing to run without them`);
    }
  } else {
    console.info(line);
  }
}

/**
 * Run a cron's main and fail the run on anything it throws, a failed Doppler load
 * included, which happens before the job's own try/catch.
 */
function runCron(main: () => Promise<void>): void {
  main().catch((error) => {
    console.error("=".repeat(80));
    console.error("❌ CRON JOB FAILED");
    console.error("Error:", error instanceof Error ? error.message : error);
    console.error("=".repeat(80));
    process.exit(1);
  });
}
