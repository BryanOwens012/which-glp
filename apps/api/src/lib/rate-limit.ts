/**
 * Per-IP rate limiting, backed by Redis.
 *
 * Two independent budgets:
 *
 * - **api** — requests to `/trpc`. Generous, because carrier-grade NAT and
 *   office networks put many genuine users behind a single address and the
 *   frontend prefetches aggressively.
 * - **unknownPath** — requests to paths this service does not serve. Tight: a
 *   real client never walks unknown paths on an API host, so exhausting this
 *   budget is a reliable signal of a vulnerability scanner. Exhausting it
 *   blocks the address outright for a cooldown, which is what stops a spray
 *   after a handful of requests instead of several hundred.
 *
 * Redis (not in-process state) is the store because the service runs multiple
 * replicas: a per-process counter would grant each caller one budget *per
 * replica* and would reset on every deploy.
 *
 * ## Failure behavior
 *
 * If Redis is unavailable this limiter **fails open** to a smaller in-process
 * budget rather than rejecting traffic. This is a deliberate exception to the
 * repo's fail-closed default: this limiter guards *availability*, not access
 * (the API is entirely public and unauthenticated), so failing closed would
 * turn a Redis blip into a total outage of the site — a worse outcome than the
 * abuse it is meant to prevent. The in-process fallback keeps a real ceiling in
 * place per replica, and every degradation is logged.
 *
 * Note that `redis.ts` stops reconnecting after three failed attempts and marks
 * Redis unavailable for the rest of the process, so a replica that loses Redis
 * for a couple of seconds stays on the in-process budget until it restarts.
 */

import { config } from './config.js'
import { getRedisClient } from './redis.js'

export const RATE_LIMIT_KINDS = ['api', 'unknownPath'] as const
export type RateLimitKind = (typeof RATE_LIMIT_KINDS)[number]

export type RateLimitDecision = {
  isAllowed: boolean
  limit: number
  remaining: number
  /** Seconds the caller should wait before retrying. Only meaningful when blocked. */
  retryAfterSeconds: number
  /** True when the decision came from the in-process fallback (Redis unavailable). */
  isDegraded: boolean
}

/**
 * Increment a counter and set its expiry in one atomic step, returning both the
 * new count and the remaining TTL.
 *
 * Doing this as separate INCR and EXPIRE commands leaves a window where a
 * process death between them strands a key with no expiry — that address would
 * then be limited forever.
 */
const INCREMENT_WINDOW_SCRIPT = `
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return {current, redis.call('TTL', KEYS[1])}
`

/** Bound on in-process map sizes, so the limiter can never itself exhaust memory. */
const MAX_TRACKED_ADDRESSES = 10_000

type FallbackEntry = { count: number; resetAtMs: number }

const fallbackCounters = new Map<string, FallbackEntry>()
/** Locally-known blocks, so a spray does not cost a Redis round trip per request. */
const blockedUntilMs = new Map<string, number>()

/**
 * Drop expired entries, and if the map is still oversized, clear it entirely.
 *
 * Clearing loses in-flight counts (briefly permissive) but is strictly bounded;
 * letting the map grow with attacker-chosen keys would not be.
 */
const pruneMap = <T>(map: Map<string, T>, isExpired: (value: T) => boolean): void => {
  if (map.size <= MAX_TRACKED_ADDRESSES) {
    return
  }

  for (const [key, value] of map) {
    if (isExpired(value)) {
      map.delete(key)
    }
  }

  if (map.size > MAX_TRACKED_ADDRESSES) {
    map.clear()
  }
}

const consumeFallbackBudget = (
  key: string,
  limit: number,
  windowSeconds: number,
): RateLimitDecision => {
  const now = Date.now()
  const existing = fallbackCounters.get(key)

  const entry =
    existing && existing.resetAtMs > now
      ? { count: existing.count + 1, resetAtMs: existing.resetAtMs }
      : { count: 1, resetAtMs: now + windowSeconds * 1000 }

  fallbackCounters.set(key, entry)
  pruneMap(fallbackCounters, (value) => value.resetAtMs <= now)

  return {
    isAllowed: entry.count <= limit,
    limit,
    remaining: Math.max(0, limit - entry.count),
    retryAfterSeconds: Math.max(1, Math.ceil((entry.resetAtMs - now) / 1000)),
    isDegraded: true,
  }
}

/**
 * Record that an address is blocked, in Redis and in the local cache.
 *
 * Best-effort: a Redis failure still leaves the local block in place on this
 * replica, which is where the spray is currently landing.
 */
export const blockAddress = async (ip: string, seconds: number): Promise<void> => {
  blockedUntilMs.set(ip, Date.now() + seconds * 1000)
  pruneMap(blockedUntilMs, (expiry) => expiry <= Date.now())

  const client = getRedisClient()

  if (!client) {
    return
  }

  try {
    await client.set(`ratelimit:blocked:${ip}`, '1', 'EX', seconds)
  } catch (error) {
    console.error(
      '❌ Rate limit: failed to persist block:',
      error instanceof Error ? error.message : String(error),
    )
  }
}

/**
 * Whether an address is currently blocked.
 *
 * Checks the local cache first so a spray in progress is rejected without a
 * network round trip per request.
 */
export const isAddressBlocked = async (ip: string): Promise<boolean> => {
  const localExpiry = blockedUntilMs.get(ip)

  if (localExpiry !== undefined) {
    if (localExpiry > Date.now()) {
      return true
    }

    blockedUntilMs.delete(ip)
  }

  const client = getRedisClient()

  if (!client) {
    return false
  }

  try {
    const blocked = await client.get(`ratelimit:blocked:${ip}`)

    if (!blocked) {
      return false
    }

    // Mirror the block locally so sibling replicas also stop paying for lookups.
    const ttl = await client.ttl(`ratelimit:blocked:${ip}`)

    if (ttl > 0) {
      blockedUntilMs.set(ip, Date.now() + ttl * 1000)
    }

    return true
  } catch (error) {
    console.error(
      '❌ Rate limit: block lookup failed:',
      error instanceof Error ? error.message : String(error),
    )
    return false
  }
}

/**
 * Consume one unit of an address's budget.
 *
 * @param ip - the client address, as resolved from the proxy chain
 * @param kind - which budget to draw from
 * @returns the decision, including headers-worthy limit/remaining/retry values
 */
export const consumeRateLimit = async (
  ip: string,
  kind: RateLimitKind,
): Promise<RateLimitDecision> => {
  const settings =
    kind === 'api' ? config.rateLimit.api : config.rateLimit.unknownPath

  const { windowSeconds, maxRequests } = settings
  const client = getRedisClient()

  if (!client) {
    return consumeFallbackBudget(`${kind}:${ip}`, maxRequests, windowSeconds)
  }

  try {
    // Bucket the key by window so counts reset cleanly and keys self-expire.
    const windowIndex = Math.floor(Date.now() / 1000 / windowSeconds)
    const key = `ratelimit:${kind}:${ip}:${windowIndex}`

    const [count, ttl] = (await client.eval(
      INCREMENT_WINDOW_SCRIPT,
      1,
      key,
      String(windowSeconds),
    )) as [number, number]

    return {
      isAllowed: count <= maxRequests,
      limit: maxRequests,
      remaining: Math.max(0, maxRequests - count),
      retryAfterSeconds: ttl > 0 ? ttl : windowSeconds,
      isDegraded: false,
    }
  } catch (error) {
    console.error(
      '❌ Rate limit: Redis check failed, falling back to in-process budget:',
      error instanceof Error ? error.message : String(error),
    )
    return consumeFallbackBudget(`${kind}:${ip}`, maxRequests, windowSeconds)
  }
}

/** Reset all in-process state. Test-only. */
export const resetRateLimitStateForTests = (): void => {
  fallbackCounters.clear()
  blockedUntilMs.clear()
}
