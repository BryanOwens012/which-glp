import { afterEach, describe, expect, it, vi } from 'vitest'
import { installConsoleRedaction, redactSupabaseSecrets } from './redact.js'

describe('redactSupabaseSecrets', () => {
  it('masks every secret key in a string', () => {
    expect(redactSupabaseSecrets('a sb_secret_abc-1_2 b sb_secret_xyz')).toBe(
      'a sb_secret_[REDACTED] b sb_secret_[REDACTED]',
    )
  })

  it('leaves publishable keys and plain text alone', () => {
    expect(redactSupabaseSecrets('sb_publishable_abc ok')).toBe('sb_publishable_abc ok')
  })
})

describe('installConsoleRedaction', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('masks secret keys in strings and errors passed to console', () => {
    const written: unknown[][] = []
    // Stub the underlying method before installing, so the wrapper calls the stub.
    vi.spyOn(console, 'error').mockImplementation((...args: unknown[]) => {
      written.push(args)
    })
    installConsoleRedaction()

    console.error('key=sb_secret_live123', new Error('bad key sb_secret_live123'), { n: 1 })

    expect(written).toHaveLength(1)
    const [text, error, object] = written[0]
    expect(text).toBe('key=sb_secret_[REDACTED]')
    expect((error as Error).message).toBe('bad key sb_secret_[REDACTED]')
    expect((error as Error).stack).not.toContain('sb_secret_live123')
    expect(object).toEqual({ n: 1 })
  })
})
