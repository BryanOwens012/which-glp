/**
 * The trigger crons in `.railway/functions` fail closed on INTERNAL_API_KEY: without a
 * usable key they never call their service, and a rejected call is a failed run.
 *
 * Each cron runs as Railway ships it, the Doppler loader prepended to its own file
 * (see `buildFunctionSource` in `.railway/railway.ts`), type-stripped, with `fetch`,
 * `process` and `setTimeout` passed in as stand-ins.
 */
import { readFileSync } from 'node:fs'
import { stripTypeScriptTypes } from 'node:module'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it, vi } from 'vitest'

const FUNCTIONS_DIR = new URL('../../../../.railway/functions/', import.meta.url)
const CRONS = ['post-ingestion-cron.ts', 'post-extraction-cron.ts', 'user-extraction-cron.ts'] as const

const readFunction = (file: string): string => readFileSync(fileURLToPath(new URL(file, FUNCTIONS_DIR)), 'utf8')

/** Run one cron with a fake service; resolves with the exit code it chose and the service calls. */
const runCron = async (file: string, env: Record<string, string>, status: number) => {
  const source = stripTypeScriptTypes(`${readFunction('_doppler-secrets.ts')}\n${readFunction(file)}`)
  const calls: { url: string; key: string | null }[] = []
  const fetchFn = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(input), key: new Headers(init?.headers).get('x-internal-api-key') })
    return new Response(JSON.stringify({ ok: status < 400 }), { status })
  })
  const exitCode = await new Promise<number>((resolve) => {
    const fakeProcess = { env, exit: (code: number) => resolve(code) }
    new Function('fetch', 'process', 'setTimeout', source)(fetchFn, fakeProcess, setTimeout)
  })
  return { exitCode, calls }
}

describe.each(CRONS)('%s', (file) => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  const quiet = () => {
    for (const level of ['log', 'info', 'warn', 'error'] as const) {
      vi.spyOn(console, level).mockImplementation(() => {})
    }
  }

  it('refuses to call its service without INTERNAL_API_KEY', async () => {
    quiet()
    const { exitCode, calls } = await runCron(file, {}, 200)

    expect(exitCode).toBe(1)
    expect(calls).toEqual([])
  })

  it('refuses a key containing whitespace', async () => {
    quiet()
    const { exitCode, calls } = await runCron(file, { INTERNAL_API_KEY: 'key\n' }, 200)

    expect(exitCode).toBe(1)
    expect(calls).toEqual([])
  })

  it('fails the run when the service rejects the key', async () => {
    quiet()
    const { exitCode, calls } = await runCron(file, { INTERNAL_API_KEY: 'k' }, 403)

    expect(exitCode).toBe(1)
    expect(calls).toHaveLength(1)
  })

  it('sends the key and succeeds when the service accepts it', async () => {
    quiet()
    const { exitCode, calls } = await runCron(file, { INTERNAL_API_KEY: 'k' }, 200)

    expect(exitCode).toBe(0)
    expect(calls.map((call) => call.key)).toEqual(['k'])
  })
})
