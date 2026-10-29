/**
 * Load this service's secrets from Doppler at boot, and report what arrived.
 *
 * Each backend service fetches only the secret names it enumerates, one request per
 * name, with the environment's single DOPPLER_TOKEN (plus DOPPLER_PROJECT and
 * DOPPLER_CONFIG). Pulled values are written into `process.env` for this process
 * only, overriding any Railway-provided copy; nothing outside the enumerated list is
 * requested or accepted. The boot log gives how many were pulled and how many failed,
 * with both name lists and a reason per failure, never a value. Without
 * DOPPLER_TOKEN (local development) the load is skipped and `.env` applies as before.
 *
 * Backend only: the frontend reads public `NEXT_PUBLIC_*` config from ordinary
 * environment variables and never talks to Doppler.
 *
 * The Python services keep the same loader in
 * `scripts/legacy-ingestion/shared/doppler_secrets.py`, and the cron functions in
 * `.railway/functions/_doppler-secrets.ts`; keep the three in sync, log format
 * included.
 *
 * API reference: https://docs.doppler.com/reference/secrets-get
 */

const DOPPLER_SECRET_URL = 'https://api.doppler.com/v3/configs/config/secret'

/** A secret name as Doppler and the shell accept it; anything else is never requested. */
const SECRET_NAME_PATTERN = /^[A-Z][A-Z0-9_]*$/

const REQUEST_TIMEOUT_MS = 5_000

/** Attempts per secret; 429 and 5xx responses and network errors are retried. */
const MAX_ATTEMPTS = 3

const RETRY_BASE_DELAY_MS = 250

/** A Retry-After header is honored up to this cap. */
const MAX_RETRY_AFTER_MS = 5_000

export type DopplerFailure = { name: string; reason: string }

export type DopplerLoadReport = {
  pulled: string[]
  failed: DopplerFailure[]
}

type FetchOutcome = { name: string; value: string } | DopplerFailure

type LoadDeps = {
  env: Record<string, string | undefined>
  fetchFn: typeof fetch
  sleep: (ms: number) => Promise<void>
}

const defaultDeps: LoadDeps = {
  env: process.env,
  fetchFn: fetch,
  sleep: async (ms) => {
    await new Promise((resolve) => setTimeout(resolve, ms))
  },
}

const isRetryable = (status: number): boolean => status === 429 || status >= 500

/** Exponential backoff with jitter, or the server's Retry-After (seconds) up to a cap. */
const getRetryDelayMs = (attempt: number, retryAfter: string | null): number => {
  // An empty header would read as 0 seconds; treat it like a missing one.
  const seconds = retryAfter === null || retryAfter.trim() === '' ? Number.NaN : Number(retryAfter)
  if (Number.isFinite(seconds)) {
    return Math.min(Math.max(seconds * 1000, 0), MAX_RETRY_AFTER_MS)
  }
  return RETRY_BASE_DELAY_MS * 4 ** (attempt - 1) * (1 + Math.random() * 0.5)
}

const buildSecretUrl = (name: string, env: LoadDeps['env']): string => {
  const params = new URLSearchParams({ name })
  if (env.DOPPLER_PROJECT) {
    params.set('project', env.DOPPLER_PROJECT)
  }
  if (env.DOPPLER_CONFIG) {
    params.set('config', env.DOPPLER_CONFIG)
  }
  return `${DOPPLER_SECRET_URL}?${params.toString()}`
}

/** Fetch one secret: its computed value, or why it could not be pulled. */
const fetchSecret = async (name: string, token: string, deps: LoadDeps): Promise<FetchOutcome> => {
  let lastReason = 'error network'
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    let retryAfter: string | null = null
    try {
      const response = await deps.fetchFn(buildSecretUrl(name, deps.env), {
        headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
        // Never follow a redirect, so the token is only ever sent to Doppler.
        redirect: 'error',
      })
      if (response.ok) {
        const body = (await response.json()) as { value?: { computed?: unknown } } | null
        const value = body?.value?.computed
        if (typeof value !== 'string' || value === '') {
          return { name, reason: 'empty' }
        }
        return { name, value }
      }
      if (response.status === 404) {
        return { name, reason: 'not_found' }
      }
      lastReason = `error ${response.status}`
      if (!isRetryable(response.status)) {
        return { name, reason: lastReason }
      }
      retryAfter = response.headers.get('retry-after')
    } catch {
      lastReason = 'error network'
    }
    if (attempt < MAX_ATTEMPTS) {
      await deps.sleep(getRetryDelayMs(attempt, retryAfter))
    }
  }
  return { name, reason: lastReason }
}

/** One log line: counts, then the pulled names, then the failed names with reasons. */
export const formatDopplerReport = (report: DopplerLoadReport): string => {
  const expected = report.pulled.length + report.failed.length
  const failed = report.failed.map(({ name, reason }) => `${name} (${reason})`)
  return `[doppler] pulled ${report.pulled.length} of ${expected} secrets, ${report.failed.length} failed; pulled=${JSON.stringify(report.pulled)} failed=${JSON.stringify(failed)}`
}

/**
 * Fetch `names` from Doppler, write the pulled values into `deps.env`, and log the
 * report: info when every secret arrived, warn when any failed. Returns null, after
 * logging a skip, when DOPPLER_TOKEN is not set.
 */
export const loadDopplerSecrets = async (
  names: readonly string[],
  deps: Partial<LoadDeps> = {},
): Promise<DopplerLoadReport | null> => {
  const resolved: LoadDeps = { ...defaultDeps, ...deps }
  const token = resolved.env.DOPPLER_TOKEN
  if (!token) {
    // On Railway every service is given DOPPLER_TOKEN, so its absence is a misconfiguration.
    if (resolved.env.RAILWAY_ENVIRONMENT_NAME) {
      console.warn('[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (running on existing environment values)')
    } else {
      console.info('[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (local .env applies)')
    }
    return null
  }

  const unique = [...new Set(names)].sort()
  const report: DopplerLoadReport = { pulled: [], failed: [] }
  const requested = unique.filter((name) => {
    if (SECRET_NAME_PATTERN.test(name)) {
      return true
    }
    report.failed.push({ name, reason: 'invalid_name' })
    return false
  })

  const outcomes = await Promise.all(requested.map((name) => fetchSecret(name, token, resolved)))
  for (const outcome of outcomes) {
    if ('value' in outcome) {
      resolved.env[outcome.name] = outcome.value
      report.pulled.push(outcome.name)
    } else {
      report.failed.push(outcome)
    }
  }
  // Plain string order: the same as the Python loader's sort for the ASCII names it requests.
  report.failed.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))

  const line = formatDopplerReport(report)
  if (report.failed.length > 0) {
    console.warn(line)
  } else {
    console.info(line)
  }
  return report
}
