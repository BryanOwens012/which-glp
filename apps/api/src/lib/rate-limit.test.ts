import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * Redis is mocked rather than connected to: these tests assert the limiter's
 * own decision logic, and a real connection would make them order-dependent,
 * unable to run in parallel, and would leak a client per file.
 */
const mockRedisClient = vi.hoisted(() => ({
  client: null as null | {
    eval: ReturnType<typeof vi.fn>
    get: ReturnType<typeof vi.fn>
    set: ReturnType<typeof vi.fn>
    ttl: ReturnType<typeof vi.fn>
  },
}))

vi.mock('./redis.js', () => ({
  getRedisClient: () => mockRedisClient.client,
}))

const {
  blockAddress,
  consumeRateLimit,
  isAddressBlocked,
  resetRateLimitStateForTests,
} = await import('./rate-limit.js')
const { config } = await import('./config.js')

const makeClient = () => ({
  eval: vi.fn(),
  get: vi.fn().mockResolvedValue(null),
  set: vi.fn().mockResolvedValue('OK'),
  ttl: vi.fn().mockResolvedValue(-1),
})

beforeEach(() => {
  resetRateLimitStateForTests()
  mockRedisClient.client = null
  vi.restoreAllMocks()
  // The limiter logs on degradation and on blocks; keep test output readable.
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(console, 'warn').mockImplementation(() => {})
})

afterEach(() => {
  vi.useRealTimers()
  resetRateLimitStateForTests()
})

describe('consumeRateLimit with Redis available', () => {
  it('allows a request within the budget and reports what remains', async () => {
    const client = makeClient()
    client.eval.mockResolvedValue([1, 60])
    mockRedisClient.client = client

    const decision = await consumeRateLimit('203.0.113.1', 'api')

    expect(decision.isAllowed).toBe(true)
    expect(decision.limit).toBe(config.rateLimit.api.maxRequests)
    expect(decision.remaining).toBe(config.rateLimit.api.maxRequests - 1)
    expect(decision.isDegraded).toBe(false)
  })

  it('denies once the count exceeds the budget', async () => {
    const client = makeClient()
    client.eval.mockResolvedValue([config.rateLimit.api.maxRequests + 1, 42])
    mockRedisClient.client = client

    const decision = await consumeRateLimit('203.0.113.1', 'api')

    expect(decision.isAllowed).toBe(false)
    expect(decision.remaining).toBe(0)
    expect(decision.retryAfterSeconds).toBe(42)
  })

  it('allows exactly the budget, denying only the request past it', async () => {
    const client = makeClient()
    mockRedisClient.client = client

    client.eval.mockResolvedValue([config.rateLimit.unknownPath.maxRequests, 600])
    await expect(
      consumeRateLimit('203.0.113.1', 'unknownPath').then((d) => d.isAllowed),
    ).resolves.toBe(true)

    client.eval.mockResolvedValue([config.rateLimit.unknownPath.maxRequests + 1, 600])
    await expect(
      consumeRateLimit('203.0.113.1', 'unknownPath').then((d) => d.isAllowed),
    ).resolves.toBe(false)
  })

  it('scopes counters per address and per budget kind', async () => {
    const client = makeClient()
    client.eval.mockResolvedValue([1, 60])
    mockRedisClient.client = client

    await consumeRateLimit('203.0.113.1', 'api')
    await consumeRateLimit('203.0.113.2', 'api')
    await consumeRateLimit('203.0.113.1', 'unknownPath')

    const keys = client.eval.mock.calls.map((call) => call[2] as string)

    expect(new Set(keys).size).toBe(3)
    expect(keys[0]).toContain('ratelimit:api:203.0.113.1')
    expect(keys[2]).toContain('ratelimit:unknownPath:203.0.113.1')
  })

  it('falls back to the in-process budget when Redis throws', async () => {
    const client = makeClient()
    client.eval.mockRejectedValue(new Error('ECONNREFUSED'))
    mockRedisClient.client = client

    const decision = await consumeRateLimit('203.0.113.1', 'api')

    // Fails open to a real ceiling rather than rejecting live traffic.
    expect(decision.isAllowed).toBe(true)
    expect(decision.isDegraded).toBe(true)
  })
})

describe('consumeRateLimit without Redis', () => {
  it('still enforces a ceiling in process', async () => {
    const limit = config.rateLimit.unknownPath.maxRequests

    for (let attempt = 0; attempt < limit; attempt += 1) {
      const decision = await consumeRateLimit('203.0.113.5', 'unknownPath')
      expect(decision.isAllowed).toBe(true)
      expect(decision.isDegraded).toBe(true)
    }

    const exceeded = await consumeRateLimit('203.0.113.5', 'unknownPath')
    expect(exceeded.isAllowed).toBe(false)
  })

  it('resets the budget once the window elapses', async () => {
    vi.useFakeTimers()

    const limit = config.rateLimit.unknownPath.maxRequests

    for (let attempt = 0; attempt <= limit; attempt += 1) {
      await consumeRateLimit('203.0.113.6', 'unknownPath')
    }

    expect((await consumeRateLimit('203.0.113.6', 'unknownPath')).isAllowed).toBe(false)

    vi.advanceTimersByTime((config.rateLimit.unknownPath.windowSeconds + 1) * 1000)

    expect((await consumeRateLimit('203.0.113.6', 'unknownPath')).isAllowed).toBe(true)
  })
})

describe('blocking', () => {
  it('reports an address as blocked without needing Redis', async () => {
    expect(await isAddressBlocked('203.0.113.7')).toBe(false)

    await blockAddress('203.0.113.7', 60)

    expect(await isAddressBlocked('203.0.113.7')).toBe(true)
    expect(await isAddressBlocked('203.0.113.8')).toBe(false)
  })

  it('stops reporting a block once it expires', async () => {
    vi.useFakeTimers()

    await blockAddress('203.0.113.7', 60)
    expect(await isAddressBlocked('203.0.113.7')).toBe(true)

    vi.advanceTimersByTime(61_000)

    expect(await isAddressBlocked('203.0.113.7')).toBe(false)
  })

  it('persists the block to Redis with a TTL so sibling replicas honor it', async () => {
    const client = makeClient()
    mockRedisClient.client = client

    await blockAddress('203.0.113.7', 3600)

    expect(client.set).toHaveBeenCalledWith(
      'ratelimit:blocked:203.0.113.7',
      '1',
      'EX',
      3600,
    )
  })

  it('picks up a block set by another replica', async () => {
    const client = makeClient()
    client.get.mockResolvedValue('1')
    client.ttl.mockResolvedValue(1800)
    mockRedisClient.client = client

    expect(await isAddressBlocked('203.0.113.9')).toBe(true)

    // Mirrored locally, so a spray in progress stops costing a round trip.
    client.get.mockClear()
    expect(await isAddressBlocked('203.0.113.9')).toBe(true)
    expect(client.get).not.toHaveBeenCalled()
  })

  it('does not block traffic when the Redis block lookup fails', async () => {
    const client = makeClient()
    client.get.mockRejectedValue(new Error('ECONNREFUSED'))
    mockRedisClient.client = client

    expect(await isAddressBlocked('203.0.113.9')).toBe(false)
  })

  it('keeps the local block even when persisting it fails', async () => {
    const client = makeClient()
    client.set.mockRejectedValue(new Error('ECONNREFUSED'))
    mockRedisClient.client = client

    await blockAddress('203.0.113.7', 60)

    // The spray is landing on this replica; losing the local block would let it continue.
    expect(await isAddressBlocked('203.0.113.7')).toBe(true)
  })
})
