// Doppler secret loader for the cron functions. `railway.ts` prepends this file to
// each function's source when encoding it, so every function gets one copy; a
// function calls `await loadDopplerSecrets(DOPPLER_SECRETS)` before its first secret
// read. Same behavior and log format as `apps/api/src/lib/doppler-secrets.ts` and
// `scripts/legacy-ingestion/shared/doppler_secrets.py`; keep the three in sync.
//
// Fetches only the enumerated names, one request each, with DOPPLER_TOKEN (and
// DOPPLER_PROJECT / DOPPLER_CONFIG); writes pulled values into process.env for this
// run only; logs pulled and failed names with reasons, never a value.

async function loadDopplerSecrets(names: readonly string[]): Promise<void> {
  const token = process.env.DOPPLER_TOKEN;
  if (!token) {
    console.info("[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (local .env applies)");
    return;
  }

  const fetchSecret = async (name: string): Promise<{ name: string; value?: string; reason?: string }> => {
    const params = new URLSearchParams({ name });
    if (process.env.DOPPLER_PROJECT) {
      params.set("project", process.env.DOPPLER_PROJECT);
    }
    if (process.env.DOPPLER_CONFIG) {
      params.set("config", process.env.DOPPLER_CONFIG);
    }
    let lastReason = "error network";
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const response = await fetch(`https://api.doppler.com/v3/configs/config/secret?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
          signal: AbortSignal.timeout(5_000),
        });
        if (response.ok) {
          const body = (await response.json()) as { value?: { computed?: unknown } };
          const value = body.value?.computed;
          return typeof value === "string" && value !== "" ? { name, value } : { name, reason: "empty" };
        }
        if (response.status === 404) {
          return { name, reason: "not_found" };
        }
        lastReason = `error ${response.status}`;
        if (!(response.status === 429 || response.status >= 500)) {
          return { name, reason: lastReason };
        }
      } catch {
        lastReason = "error network";
      }
      if (attempt < 3) {
        await new Promise((resolve) => setTimeout(resolve, 250 * 4 ** (attempt - 1)));
      }
    }
    return { name, reason: lastReason };
  };

  const unique = [...new Set(names)].sort();
  const pulled: string[] = [];
  const failed: { name: string; reason: string }[] = [];
  const requested = unique.filter((name) => {
    if (/^[A-Z][A-Z0-9_]*$/.test(name)) {
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
  failed.sort((a, b) => a.name.localeCompare(b.name));

  const line = `[doppler] pulled ${pulled.length} of ${pulled.length + failed.length} secrets, ${failed.length} failed; pulled=${JSON.stringify(pulled)} failed=${JSON.stringify(failed.map(({ name, reason }) => `${name} (${reason})`))}`;
  if (failed.length > 0) {
    console.warn(line);
  } else {
    console.info(line);
  }
}
