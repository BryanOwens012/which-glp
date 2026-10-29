// Fail-closed calls from the cron functions to the internal services. `railway.ts`
// prepends this file, after the Doppler loader, to each function's source, so every
// function gets one copy; a trigger cron calls callInternalService after awaiting
// loadDopplerSecrets.
//
// The call never goes out without a usable INTERNAL_API_KEY (present, printable ASCII,
// no whitespace), and an error answer throws, so a rejected key fails the run instead
// of reading as success. A 409 means the service is already running that job: the
// response is returned and the run is a skip, not a failure. Same key rule as
// `parseInternalApiKey` (apps/api/src/lib/config.ts) and
// `scripts/legacy-ingestion/shared/internal_api_key.py`; keep the three in sync.

async function callInternalService(url: string, body: unknown): Promise<Response> {
  const internalApiKey = process.env.INTERNAL_API_KEY;
  if (!internalApiKey || !/^[\x21-\x7e]+$/.test(internalApiKey)) {
    throw new Error("INTERNAL_API_KEY is missing or is not printable ASCII without whitespace; refusing to call the service");
  }
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-internal-api-key": internalApiKey },
    body: JSON.stringify(body),
    redirect: "error", // never follow a redirect, so the key only goes to the service named
  });
  if (!response.ok && response.status !== 409) {
    throw new Error(`Service responded ${response.status} ${response.statusText}`);
  }
  return response;
}
