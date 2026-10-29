import { describe, expect, it } from 'vitest'
import { installConsoleRedaction, redactSupabaseSecrets } from './redact.js'

const METHODS = ['log', 'info', 'warn', 'error', 'debug'] as const

/** A console stand-in that records what each method was called with. */
const makeRecordingConsole = () => {
  const calls: { method: string; args: unknown[] }[] = []
  const record =
    (method: string) =>
    (...args: unknown[]) => {
      calls.push({ method, args })
    }
  const target: Pick<Console, (typeof METHODS)[number]> = {
    log: record('log'),
    info: record('info'),
    warn: record('warn'),
    error: record('error'),
    debug: record('debug'),
  }
  return { target, calls }
}

class PostgrestLikeError extends Error {
  code = 'PGRST301'
  details = 'header apikey=sb_secret_live123'
}

describe('redactSupabaseSecrets', () => {
  it('masks every secret key in a string', () => {
    expect(redactSupabaseSecrets('a sb_secret_abc-1_2 b sb_secret_xyz')).toBe(
      'a sb_secret_[REDACTED] b sb_secret_[REDACTED]',
    )
  })

  it('masks the whole of any key the validator accepts', () => {
    expect(redactSupabaseSecrets('k=sb_secret_ab.c+d/e= end')).toBe('k=sb_secret_[REDACTED] end')
  })

  it('leaves publishable keys and plain text alone', () => {
    expect(redactSupabaseSecrets('sb_publishable_abc ok')).toBe('sb_publishable_abc ok')
  })
})

describe('installConsoleRedaction', () => {
  it.each(METHODS)('masks secret keys passed to console.%s', (method) => {
    const { target, calls } = makeRecordingConsole()
    installConsoleRedaction(target)

    target[method]('key=sb_secret_live123', { n: 1 })

    expect(calls).toEqual([{ method, args: ['key=sb_secret_[REDACTED]', { n: 1 }] }])
  })

  it('masks errors while keeping their class, fields, and cause', () => {
    const { target, calls } = makeRecordingConsole()
    installConsoleRedaction(target)
    const error = new PostgrestLikeError('bad key sb_secret_live123', {
      cause: new Error('inner sb_secret_live123'),
    })

    target.error(error)

    const logged = calls[0].args[0] as PostgrestLikeError
    expect(logged).toBeInstanceOf(PostgrestLikeError)
    expect(logged.message).toBe('bad key sb_secret_[REDACTED]')
    expect(logged.stack).not.toContain('sb_secret_live123')
    expect(logged.code).toBe('PGRST301')
    expect(logged.details).toBe('header apikey=sb_secret_[REDACTED]')
    expect((logged.cause as Error).message).toBe('inner sb_secret_[REDACTED]')
    expect(error.message).toBe('bad key sb_secret_live123')
  })

  it('survives a self-referencing cause', () => {
    const { target, calls } = makeRecordingConsole()
    installConsoleRedaction(target)
    const error = new Error('loop sb_secret_live123')
    Object.defineProperty(error, 'cause', { value: error })

    target.error(error)

    const logged = calls[0].args[0] as Error
    expect(logged.message).toBe('loop sb_secret_[REDACTED]')
    expect(logged.cause).toBe(logged)
  })

  it('wraps a target only once', () => {
    const { target, calls } = makeRecordingConsole()
    installConsoleRedaction(target)
    const wrapped = target.log
    installConsoleRedaction(target)

    expect(target.log).toBe(wrapped)
    target.log('x')
    expect(calls).toHaveLength(1)
  })
})
