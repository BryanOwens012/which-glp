import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { formatDopplerReport, loadDopplerSecrets } from './doppler-secrets.js'

type Reply = { status: number; computed?: string } | 'network'

/** A fake fetch answering each secret name from a script of replies, recording every request. */
const makeFetch = (script: Record<string, Reply[]>) => {
  const requests: { name: string; url: URL; auth: string | null }[] = []
  const fetchFn = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    const url = new URL(String(input))
    const name = url.searchParams.get('name') ?? ''
    requests.push({ name, url, auth: new Headers(init?.headers).get('authorization') })
    const reply = script[name]?.shift() ?? { status: 404 }
    if (reply === 'network') {
      throw new TypeError('fetch failed')
    }
    const body = reply.computed === undefined ? {} : { name, value: { computed: reply.computed } }
    return new Response(JSON.stringify(body), { status: reply.status })
  })
  return { fetchFn: fetchFn as unknown as typeof fetch, requests }
}

const noSleep = async () => {}

const baseEnv = (): Record<string, string | undefined> => ({
  DOPPLER_TOKEN: 'dp.st.prd.test-token',
  DOPPLER_PROJECT: 'whichglp',
  DOPPLER_CONFIG: 'prd',
})

describe('loadDopplerSecrets', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('pulls each enumerated secret into env and reports pulled and failed names', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const env: Record<string, string | undefined> = { ...baseEnv(), SUPABASE_URL: 'railway-copy' }
    const { fetchFn, requests } = makeFetch({
      SUPABASE_URL: [{ status: 200, computed: 'https://x.supabase.co' }],
      INTERNAL_API_KEY: [{ status: 200, computed: 'k' }],
      MISSING_ONE: [{ status: 404 }],
    })

    const report = await loadDopplerSecrets(['SUPABASE_URL', 'INTERNAL_API_KEY', 'MISSING_ONE'], {
      env,
      fetchFn,
      sleep: noSleep,
    })

    expect(report).toEqual({
      pulled: ['INTERNAL_API_KEY', 'SUPABASE_URL'],
      failed: [{ name: 'MISSING_ONE', reason: 'not_found' }],
    })
    expect(env.SUPABASE_URL).toBe('https://x.supabase.co')
    expect(env.INTERNAL_API_KEY).toBe('k')
    expect(env.MISSING_ONE).toBeUndefined()
    expect(requests.map((r) => r.name).sort()).toEqual(['INTERNAL_API_KEY', 'MISSING_ONE', 'SUPABASE_URL'])
    expect(requests.every((r) => r.auth === 'Bearer dp.st.prd.test-token')).toBe(true)
    expect(requests[0].url.searchParams.get('project')).toBe('whichglp')
    expect(requests[0].url.searchParams.get('config')).toBe('prd')
  })

  it('requests only the enumerated names, never another secret', async () => {
    vi.spyOn(console, 'info').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({ A: [{ status: 200, computed: 'a' }] })

    await loadDopplerSecrets(['A'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(requests.map((r) => r.name)).toEqual(['A'])
  })

  it('retries 429 and 5xx, then succeeds', async () => {
    vi.spyOn(console, 'info').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({
      A: [{ status: 429 }, { status: 503 }, { status: 200, computed: 'a' }],
    })

    const report = await loadDopplerSecrets(['A'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(report?.pulled).toEqual(['A'])
    expect(requests).toHaveLength(3)
  })

  it('does not retry a client error such as 401', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({ A: [{ status: 401 }, { status: 200, computed: 'a' }] })

    const report = await loadDopplerSecrets(['A'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(report?.failed).toEqual([{ name: 'A', reason: 'error 401' }])
    expect(requests).toHaveLength(1)
  })

  it('gives up after repeated network errors', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({ A: ['network', 'network', 'network', { status: 200, computed: 'a' }] })

    const report = await loadDopplerSecrets(['A'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(report?.failed).toEqual([{ name: 'A', reason: 'error network' }])
    expect(requests).toHaveLength(3)
  })

  it('treats an empty value as failed and leaves the existing env value', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const env: Record<string, string | undefined> = { ...baseEnv(), A: 'railway-copy' }
    const { fetchFn } = makeFetch({ A: [{ status: 200, computed: '' }] })

    const report = await loadDopplerSecrets(['A'], { env, fetchFn, sleep: noSleep })

    expect(report?.failed).toEqual([{ name: 'A', reason: 'empty' }])
    expect(env.A).toBe('railway-copy')
  })

  it('never requests a name that is not shaped like an environment variable', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({})

    const report = await loadDopplerSecrets(['bad name'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(report?.failed).toEqual([{ name: 'bad name', reason: 'invalid_name' }])
    expect(requests).toHaveLength(0)
  })

  it('skips without a token and makes no request', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({})

    const report = await loadDopplerSecrets(['A'], { env: {}, fetchFn, sleep: noSleep })

    expect(report).toBeNull()
    expect(requests).toHaveLength(0)
    expect(String(info.mock.calls[0][0])).toContain('DOPPLER_TOKEN is not set')
  })

  it('logs the counts and names at warn on any failure, and never a value', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn } = makeFetch({ A: [{ status: 200, computed: 'secret-value-a' }], B: [{ status: 404 }] })

    await loadDopplerSecrets(['A', 'B'], { env: baseEnv(), fetchFn, sleep: noSleep })

    const line = String(warn.mock.calls[0][0])
    expect(line).toBe('[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["A"] failed=["B (not_found)"]')
    expect(line).not.toContain('secret-value-a')
  })
})

describe('loadDopplerSecrets hardening', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('honors Retry-After, capped', async () => {
    vi.spyOn(console, 'info').mockImplementation(() => {})
    const replies = [
      new Response('{}', { status: 429, headers: { 'Retry-After': '2' } }),
      new Response('{}', { status: 503, headers: { 'Retry-After': '120' } }),
      new Response(JSON.stringify({ value: { computed: 'a' } }), { status: 200 }),
    ]
    const fetchFn = vi.fn(async () => replies.shift() as Response) as unknown as typeof fetch
    const delays: number[] = []

    const report = await loadDopplerSecrets(['A'], {
      env: baseEnv(),
      fetchFn,
      sleep: async (ms) => {
        delays.push(ms)
      },
    })

    expect(report?.pulled).toEqual(['A'])
    expect(delays).toEqual([2000, 5000])
  })

  it('warns when DOPPLER_TOKEN is missing on Railway', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({})

    await loadDopplerSecrets(['A'], { env: { RAILWAY_ENVIRONMENT_NAME: 'production' }, fetchFn, sleep: noSleep })

    expect(requests).toHaveLength(0)
    expect(String(warn.mock.calls[0][0])).toContain('DOPPLER_TOKEN is not set')
  })
})

/** Shared with the Python suite, so both loaders are held to one log format. */
const GOLDEN_CASES = JSON.parse(
  readFileSync(
    fileURLToPath(new URL('../../../../scripts/legacy-ingestion/tests/fixtures/doppler-log-format.json', import.meta.url)),
    'utf8',
  ),
) as { pulled: string[]; failed: { name: string; reason: string }[]; line: string }[]

describe('formatDopplerReport', () => {
  it.each(GOLDEN_CASES)('matches the shared golden line: $line', ({ pulled, failed, line }) => {
    expect(formatDopplerReport({ pulled, failed })).toBe(line)
  })
})

describe('loadDopplerSecrets ordering', () => {
  it('sorts failures in code-point order, like the Python loader', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn } = makeFetch({})

    const report = await loadDopplerSecrets(['Z', 'A_B', 'AB'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(report?.failed.map((f) => f.name)).toEqual(['AB', 'A_B', 'Z'])
    vi.restoreAllMocks()
  })
})

describe('loadDopplerSecrets timing', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('backs off with jitter between attempts and not after the last', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const { fetchFn } = makeFetch({ A: [{ status: 503 }, { status: 503 }, { status: 503 }] })
    const delays: number[] = []

    await loadDopplerSecrets(['A'], {
      env: baseEnv(),
      fetchFn,
      sleep: async (ms) => {
        delays.push(ms)
      },
    })

    expect(delays).toHaveLength(2)
    expect(delays[0]).toBeGreaterThanOrEqual(250)
    expect(delays[0]).toBeLessThanOrEqual(375)
    expect(delays[1]).toBeGreaterThanOrEqual(1000)
    expect(delays[1]).toBeLessThanOrEqual(1500)
  })

  it('bounds every request with a timeout signal', async () => {
    vi.spyOn(console, 'info').mockImplementation(() => {})
    const signals: (AbortSignal | null | undefined)[] = []
    const fetchFn = vi.fn(async (_input: string | URL | Request, init?: RequestInit) => {
      signals.push(init?.signal)
      return new Response(JSON.stringify({ value: { computed: 'a' } }), { status: 200 })
    }) as unknown as typeof fetch

    await loadDopplerSecrets(['A'], { env: baseEnv(), fetchFn, sleep: noSleep })

    expect(signals).toHaveLength(1)
    expect(signals[0]).toBeInstanceOf(AbortSignal)
  })
})
