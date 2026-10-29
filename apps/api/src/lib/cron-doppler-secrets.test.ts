/**
 * Behavior of the cron functions' Doppler loader, `.railway/functions/_doppler-secrets.ts`.
 *
 * Railway runs that file's bytes, prepended to each function, with nothing to inject
 * dependencies through, so this test strips its types the way `.railway/check.ts`
 * does and runs it with `fetch` and `process` passed in as stand-ins.
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

/** The loader as shipped, bound to a fake fetch and environment. */
const buildLoader = (fetchFn: typeof fetch, env: Record<string, string | undefined>): CronLoader => {
  const source = stripTypeScriptTypes(readFileSync(LOADER_PATH, 'utf8'))
  return new Function('fetch', 'process', `${source}\nreturn loadDopplerSecrets;`)(fetchFn, { env }) as CronLoader
}

type Reply = { status: number; computed?: string; retryAfter?: string }

const makeFetch = (script: Record<string, Reply[]>) => {
  const requests: { name: string; url: URL; auth: string | null; redirect?: RequestRedirect }[] = []
  const fetchFn = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    const url = new URL(String(input))
    const name = url.searchParams.get('name') ?? ''
    requests.push({ name, url, auth: new Headers(init?.headers).get('authorization'), redirect: init?.redirect })
    const reply = script[name]?.shift() ?? { status: 404 }
    const body = reply.computed === undefined ? {} : { name, value: { computed: reply.computed } }
    const headers = reply.retryAfter === undefined ? undefined : { 'Retry-After': reply.retryAfter }
    return new Response(JSON.stringify(body), { status: reply.status, headers })
  })
  return { fetchFn: fetchFn as unknown as typeof fetch, requests }
}

const baseEnv = (): Record<string, string | undefined> => ({
  DOPPLER_TOKEN: 'dp.st.prd.test-token',
  DOPPLER_PROJECT: 'whichglp',
  DOPPLER_CONFIG: 'prd',
})

describe('cron Doppler loader', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('pulls, retries a 5xx, reports a 404, and logs the shared format without a value', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const env = baseEnv()
    const { fetchFn, requests } = makeFetch({
      INTERNAL_API_KEY: [{ status: 503, retryAfter: '0' }, { status: 200, computed: 'secret-value' }],
      SUPABASE_URL: [{ status: 404 }],
    })

    await buildLoader(fetchFn, env)(['SUPABASE_URL', 'INTERNAL_API_KEY'])

    expect(env.INTERNAL_API_KEY).toBe('secret-value')
    expect(env.SUPABASE_URL).toBeUndefined()
    expect(requests.filter((r) => r.name === 'INTERNAL_API_KEY')).toHaveLength(2)
    expect(requests.every((r) => r.auth === 'Bearer dp.st.prd.test-token' && r.redirect === 'error')).toBe(true)
    expect(requests[0].url.searchParams.get('project')).toBe('whichglp')
    expect(requests[0].url.searchParams.get('config')).toBe('prd')
    expect(warn.mock.calls).toEqual([
      ['[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["INTERNAL_API_KEY"] failed=["SUPABASE_URL (not_found)"]'],
    ])
  })

  it('produces each shared golden line', async () => {
    const cases = JSON.parse(readFileSync(GOLDEN_PATH, 'utf8')) as {
      pulled: string[]
      failed: { name: string; reason: string }[]
      line: string
    }[]
    for (const { pulled, failed, line } of cases) {
      const lines: string[] = []
      vi.spyOn(console, 'warn').mockImplementation((message: string) => lines.push(message))
      vi.spyOn(console, 'info').mockImplementation((message: string) => lines.push(message))
      const script: Record<string, Reply[]> = {}
      for (const name of pulled) {
        script[name] = [{ status: 200, computed: 'v' }]
      }
      for (const { name, reason } of failed) {
        if (reason === 'not_found') {
          script[name] = [{ status: 404 }]
        } else if (reason === 'empty') {
          script[name] = [{ status: 200 }]
        } else if (reason !== 'invalid_name') {
          // `error <status>`: answer every attempt with that status, without a retry delay.
          const status = Number(reason.slice('error '.length))
          script[name] = Array.from({ length: 3 }, () => ({ status, retryAfter: '0' }))
        }
      }
      await buildLoader(makeFetch(script).fetchFn, baseEnv())([...pulled, ...failed.map((f) => f.name)])
      expect(lines).toEqual([line])
      vi.restoreAllMocks()
    }
  })

  it('skips the load without a token', async () => {
    const info = vi.spyOn(console, 'info').mockImplementation(() => {})
    const { fetchFn, requests } = makeFetch({})

    await buildLoader(fetchFn, {})(['A'])

    expect(requests).toEqual([])
    expect(info).toHaveBeenCalledOnce()
  })
})
