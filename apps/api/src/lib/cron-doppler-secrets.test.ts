/**
 * Behavior of the cron functions' Doppler loader, `.railway/functions/_doppler-secrets.ts`.
 *
 * Railway runs that file's bytes, prepended to each function, with nothing to inject
 * dependencies through, so this test strips its types the way `.railway/check.ts`
 * does and runs it with `fetch`, `process` and `setTimeout` passed in as stand-ins.
 * It is the only test of that copy, so it covers the same behaviors as
 * `doppler-secrets.test.ts` covers for the API's.
 */
import { readFileSync } from 'node:fs'
import { stripTypeScriptTypes } from 'node:module'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it, vi } from 'vitest'

type CronLoader = (names: readonly string[]) => Promise<void>

const LOADER_PATH = fileURLToPath(new URL('../../../../.railway/functions/_doppler-secrets.ts', import.meta.url))
const GOLDEN_PATH = fileURLToPath(
  new URL('../../../../scripts/legacy-ingestion/tests/fixtures/doppler-log-format.json', import.meta.url),
)
const LOADER_SOURCE = stripTypeScriptTypes(readFileSync(LOADER_PATH, 'utf8'))

type GoldenCase = { pulled: string[]; failed: { name: string; reason: string }[]; line: string }
const GOLDEN_CASES = JSON.parse(readFileSync(GOLDEN_PATH, 'utf8')) as GoldenCase[]

type Reply = { status: number; computed?: string; retryAfter?: string; body?: string }

const baseEnv = (): Record<string, string | undefined> => ({
  DOPPLER_TOKEN: 'dp.st.prd.test-token',
  DOPPLER_PROJECT: 'whichglp',
  DOPPLER_CONFIG: 'prd',
})

/** A fake fetch answering each secret name from a script of replies, recording every request. */
const makeFetch = (script: Record<string, Reply[]>) => {
  const requests: { name: string; url: URL; auth: string | null; redirect?: RequestRedirect }[] = []
  const fetchFn = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    const url = new URL(String(input))
    const name = url.searchParams.get('name') ?? ''
    requests.push({ name, url, auth: new Headers(init?.headers).get('authorization'), redirect: init?.redirect })
    const reply = script[name]?.shift() ?? { status: 404 }
    const body =
      reply.body ?? JSON.stringify(reply.computed === undefined ? {} : { name, value: { computed: reply.computed } })
    const headers = reply.retryAfter === undefined ? undefined : { 'Retry-After': reply.retryAfter }
    return new Response(body, { status: reply.status, headers })
  })
  return { fetchFn: fetchFn as unknown as typeof fetch, requests }
}

/** The loader as shipped, bound to a fake fetch and environment, recording retry delays instead of waiting. */
const buildLoader = (script: Record<string, Reply[]>, env: Record<string, string | undefined> = baseEnv()) => {
  const { fetchFn, requests } = makeFetch(script)
  const delays: number[] = []
  const recordTimeout = (callback: () => void, ms: number) => {
    delays.push(ms)
    callback()
  }
  const load = new Function('fetch', 'process', 'setTimeout', `${LOADER_SOURCE}\nreturn loadDopplerSecrets;`)(
    fetchFn,
    { env },
    recordTimeout,
  ) as CronLoader
  return { load, requests, delays, env }
}

/** Collects the report lines the loader logs, at either level. */
const captureLog = (): string[] => {
  const lines: string[] = []
  vi.spyOn(console, 'warn').mockImplementation((message: string) => {
    lines.push(message)
  })
  vi.spyOn(console, 'info').mockImplementation((message: string) => {
    lines.push(message)
  })
  return lines
}

describe('cron Doppler loader', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('pulls, retries a 5xx, reports a 404, and logs the shared format without a value', async () => {
    const lines = captureLog()
    const { load, requests, env } = buildLoader({
      INTERNAL_API_KEY: [{ status: 503, retryAfter: '0' }, { status: 200, computed: 'secret-value' }],
      SUPABASE_URL: [{ status: 404 }],
    })

    await load(['SUPABASE_URL', 'INTERNAL_API_KEY'])

    expect(env.INTERNAL_API_KEY).toBe('secret-value')
    expect(env.SUPABASE_URL).toBeUndefined()
    expect(requests.filter((r) => r.name === 'INTERNAL_API_KEY')).toHaveLength(2)
    expect(requests.every((r) => r.auth === 'Bearer dp.st.prd.test-token' && r.redirect === 'error')).toBe(true)
    expect(requests[0].url.searchParams.get('project')).toBe('whichglp')
    expect(requests[0].url.searchParams.get('config')).toBe('prd')
    expect(lines).toEqual([
      '[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["INTERNAL_API_KEY"] failed=["SUPABASE_URL (not_found)"]',
    ])
  })

  it('has golden cases to check', () => {
    expect(GOLDEN_CASES.length).toBeGreaterThanOrEqual(4)
  })

  it.each(GOLDEN_CASES)('logs the golden line $line', async ({ pulled, failed, line }) => {
    const lines = captureLog()
    const script: Record<string, Reply[]> = {}
    for (const name of pulled) {
      script[name] = [{ status: 200, computed: 'v' }]
    }
    for (const { name, reason } of failed) {
      if (reason === 'empty') {
        script[name] = [{ status: 200 }]
      } else if (reason.startsWith('error ')) {
        // Answer every attempt with that status, without a retry delay.
        const status = Number(reason.slice('error '.length))
        script[name] = Array.from({ length: 3 }, () => ({ status, retryAfter: '0' }))
      }
      // not_found is the fake fetch's default reply; an invalid_name is never requested.
    }

    await buildLoader(script).load([...failed.map((f) => f.name), ...pulled])

    expect(lines).toEqual([line])
  })

  it.each([
    ['an empty object', '{}'],
    ['a null body', 'null'],
    ['a value with no computed field', '{"value":{}}'],
  ])('counts %s as empty without retrying', async (_label, body) => {
    const lines = captureLog()
    const { load, requests } = buildLoader({ A: [{ status: 200, body }] })

    await load(['A'])

    expect(requests).toHaveLength(1)
    expect(lines).toEqual(['[doppler] pulled 0 of 1 secrets, 1 failed; pulled=[] failed=["A (empty)"]'])
  })

  it('does not retry a client error', async () => {
    const lines = captureLog()
    const { load, requests } = buildLoader({ A: [{ status: 401 }, { status: 200, computed: 'a' }] })

    await load(['A'])

    expect(requests).toHaveLength(1)
    expect(lines).toEqual(['[doppler] pulled 0 of 1 secrets, 1 failed; pulled=[] failed=["A (error 401)"]'])
  })

  it('gives up after three attempts, backing off between them but not after the last', async () => {
    captureLog()
    const { load, requests, delays } = buildLoader({
      A: [{ status: 503 }, { status: 503 }, { status: 503 }, { status: 200, computed: 'a' }],
    })

    await load(['A'])

    expect(requests).toHaveLength(3)
    expect(delays).toHaveLength(2)
    expect(delays[0]).toBeGreaterThanOrEqual(250)
    expect(delays[0]).toBeLessThanOrEqual(375)
    expect(delays[1]).toBeGreaterThanOrEqual(1000)
    expect(delays[1]).toBeLessThanOrEqual(1500)
  })

  it('honors Retry-After up to a 5 s cap, and ignores an empty or non-numeric one', async () => {
    captureLog()
    const { load, delays } = buildLoader({
      A: [{ status: 429, retryAfter: '2' }, { status: 429, retryAfter: '120' }, { status: 200, computed: 'a' }],
      B: [{ status: 429, retryAfter: '' }, { status: 429, retryAfter: 'nan' }, { status: 200, computed: 'b' }],
    })

    await load(['A', 'B'])

    expect(delays).toHaveLength(4)
    expect(delays).toContain(2000)
    expect(delays).toContain(5000)
    expect(delays.filter((ms) => ms >= 250 && ms <= 1500)).toHaveLength(2)
  })

  it('requests each name once, and never an invalid one', async () => {
    const lines = captureLog()
    const { load, requests } = buildLoader({ A: [{ status: 200, computed: 'a' }] })

    await load(['A', 'A', 'bad name'])

    expect(requests.map((r) => r.name)).toEqual(['A'])
    expect(lines).toEqual([
      '[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["A"] failed=["bad name (invalid_name)"]',
    ])
  })

  it('skips the load at info without a token locally', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => {})
    const { load, requests } = buildLoader({}, {})

    await load(['A'])

    expect(requests).toEqual([])
    expect(info).toHaveBeenCalledOnce()
  })

  it('warns when the token is missing on Railway', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { load, requests } = buildLoader({}, { RAILWAY_ENVIRONMENT_NAME: 'production' })

    await load(['A'])

    expect(requests).toEqual([])
    expect(warn).toHaveBeenCalledOnce()
  })
})
