/**
 * Validated environment configuration for the API service.
 *
 * Every env var the service depends on is read and validated here, once, at
 * import time. A bad or missing value fails the process at boot with a message
 * naming the variable — never at some random depth mid-request.
 *
 * The rest of the codebase imports `config`, not `process.env`.
 */

/** Origins always allowed, regardless of environment. */
const DEFAULT_ALLOWED_ORIGINS = [
  'https://www.whichglp.com',
  'https://whichglp.com',
] as const

/** Local dev origins, allowed only when NODE_ENV !== 'production'. */
const DEV_ALLOWED_ORIGINS = [
  'http://localhost:3000',
  'http://localhost:3001',
  'http://127.0.0.1:3000',
] as const

/**
 * Vercel preview deployments for this project, e.g.
 * `https://which-glp-git-bryan-foo-bryanowens012s-projects.vercel.app`.
 *
 * Anchored at both ends so it matches the whole origin — an unanchored pattern
 * would also match `https://evil-which-glp.vercel.app.attacker.com`.
 */
const VERCEL_PREVIEW_ORIGIN = /^https:\/\/which-glp-[a-z0-9-]+\.vercel\.app$/

const parsePositiveInt = (name: string, raw: string | undefined, fallback: number): number => {
  if (raw === undefined || raw === '') {
    return fallback
  }

  const parsed = Number(raw)

  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`Invalid ${name}: expected a positive integer, got "${raw}"`)
  }

  return parsed
}

/**
 * Extra origins from `ALLOWED_ORIGINS` (comma-separated). Each must be a bare
 * scheme+host+port origin — a value carrying a path or a trailing slash never
 * matches a browser's `Origin` header, so reject it at boot rather than
 * silently allowing nothing.
 */
const parseExtraOrigins = (raw: string | undefined): string[] => {
  if (!raw) {
    return []
  }

  return raw
    .split(',')
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0)
    .map((entry) => {
      let parsed: URL

      try {
        parsed = new URL(entry)
      } catch {
        throw new Error(`Invalid ALLOWED_ORIGINS entry: "${entry}" is not a valid URL`)
      }

      if (parsed.origin !== entry) {
        throw new Error(
          `Invalid ALLOWED_ORIGINS entry: "${entry}" must be a bare origin with no path or trailing slash (expected "${parsed.origin}")`,
        )
      }

      return entry
    })
}

const isProduction = process.env.NODE_ENV === 'production'

const allowedOrigins = new Set<string>([
  ...DEFAULT_ALLOWED_ORIGINS,
  ...(isProduction ? [] : DEV_ALLOWED_ORIGINS),
  ...parseExtraOrigins(process.env.ALLOWED_ORIGINS),
])

export const config = {
  port: parsePositiveInt('PORT', process.env.PORT, 3002),
  isProduction,

  cors: {
    allowedOrigins,
    previewOriginPattern: VERCEL_PREVIEW_ORIGIN,
    /** Whether Vercel preview origins are accepted (disable to lock prod down further). */
    arePreviewOriginsAllowed: process.env.ALLOW_VERCEL_PREVIEW_ORIGINS !== 'false',
  },

  /**
   * Maximum accepted request body, in bytes. Anything larger is refused with a
   * 413 before it is buffered, so a single large POST cannot exhaust the
   * replica's memory. tRPC inputs here are small (filter params), so 1 MB is
   * already generous.
   */
  maxRequestBodyBytes: parsePositiveInt(
    'MAX_REQUEST_BODY_BYTES',
    process.env.MAX_REQUEST_BODY_BYTES,
    1_000_000,
  ),

  /**
   * How long a shutdown waits for in-flight requests to drain before exiting
   * anyway. `server.close()` does not resolve while a request is still being
   * served, so without a backstop one slow client keeps the process alive until
   * the platform SIGKILLs it — and a SIGKILL runs no cleanup at all.
   *
   * Keep this comfortably inside the platform's SIGTERM grace period.
   */
  shutdownTimeoutMs: parsePositiveInt(
    'SHUTDOWN_TIMEOUT_MS',
    process.env.SHUTDOWN_TIMEOUT_MS,
    10_000,
  ),

  rateLimit: {
    /** Set to 'false' to disable rate limiting entirely (local debugging). */
    isEnabled: process.env.RATE_LIMIT_ENABLED !== 'false',

    /**
     * Budget for real API traffic. Deliberately generous: mobile carriers and
     * offices put many genuine users behind one CGNAT address, and the
     * frontend prefetches aggressively.
     */
    api: {
      windowSeconds: parsePositiveInt(
        'RATE_LIMIT_API_WINDOW_SECONDS',
        process.env.RATE_LIMIT_API_WINDOW_SECONDS,
        60,
      ),
      maxRequests: parsePositiveInt(
        'RATE_LIMIT_API_MAX_REQUESTS',
        process.env.RATE_LIMIT_API_MAX_REQUESTS,
        300,
      ),
    },

    /**
     * Budget for requests to paths this service does not serve. A real client
     * never walks unknown paths on an API host, so this is tight — it is what
     * catches a vulnerability scanner within a fraction of a second instead of
     * letting it spray hundreds of paths.
     */
    unknownPath: {
      windowSeconds: parsePositiveInt(
        'RATE_LIMIT_PROBE_WINDOW_SECONDS',
        process.env.RATE_LIMIT_PROBE_WINDOW_SECONDS,
        600,
      ),
      maxRequests: parsePositiveInt(
        'RATE_LIMIT_PROBE_MAX_REQUESTS',
        process.env.RATE_LIMIT_PROBE_MAX_REQUESTS,
        5,
      ),
      /** How long an IP stays blocked after exhausting the probe budget. */
      blockSeconds: parsePositiveInt(
        'RATE_LIMIT_PROBE_BLOCK_SECONDS',
        process.env.RATE_LIMIT_PROBE_BLOCK_SECONDS,
        3600,
      ),
    },
  },
} as const
