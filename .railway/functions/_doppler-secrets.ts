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

const DOPPLER_SECRET_URL = "https://api.doppler.com/v3/configs/config/secret";
const DOPPLER_SECRET_NAME_PATTERN = /^[A-Z][A-Z0-9_]*$/;
const DOPPLER_REQUEST_TIMEOUT_MS = 5_000;
const DOPPLER_MAX_ATTEMPTS = 3; // 429 and 5xx responses and network errors are retried
const DOPPLER_RETRY_BASE_DELAY_MS = 250;
const DOPPLER_MAX_RETRY_AFTER_MS = 5_000; // a Retry-After header is honored up to this cap

async function loadDopplerSecrets(names: readonly string[]): Promise<void> {
  const token = process.env.DOPPLER_TOKEN;
  if (!token) {
    // On Railway every service is given DOPPLER_TOKEN, so its absence is a misconfiguration.
    if (process.env.RAILWAY_ENVIRONMENT_NAME) {
      console.warn("[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (running on existing environment values)");
    } else {
      console.info("[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (local .env applies)");
    }
    return;
  }
  // Only a service token is bound to one config; any other would read a config of Doppler's choosing.
  if (!token.startsWith("dp.st.")) {
    console.warn("[doppler] DOPPLER_TOKEN is not a service token (dp.st.); skipping the Doppler load (running on existing environment values)");
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
  for (const outcome of await Promise.all(requested.map(fetchSecret))) {
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
  } else {
    console.info(line);
  }
}
