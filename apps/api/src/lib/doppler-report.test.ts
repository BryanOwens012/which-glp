import { afterEach, describe, expect, it, vi } from 'vitest'
import { buildDopplerReport, formatDopplerReport, logDopplerReport } from './doppler-report.js'

describe('buildDopplerReport', () => {
  it('returns null when DOPPLER_VARIABLE_NAMES is unset', () => {
    expect(buildDopplerReport({ SUPABASE_URL: 'x' })).toBeNull()
  })

  it('splits pulled, unset and empty secrets, sorted and de-duplicated', () => {
    const report = buildDopplerReport({
      DOPPLER_VARIABLE_NAMES: ' SUPABASE_URL,INTERNAL_API_KEY,,MISSING_ONE, BLANK ,SUPABASE_URL',
      SUPABASE_URL: 'https://x.supabase.co',
      INTERNAL_API_KEY: 'k',
      BLANK: '',
    })

    expect(report).toEqual({
      pulled: ['INTERNAL_API_KEY', 'SUPABASE_URL'],
      failed: [
        { name: 'BLANK', reason: 'empty' },
        { name: 'MISSING_ONE', reason: 'unset' },
      ],
    })
  })

  it('treats an empty expected list as nothing to pull', () => {
    expect(buildDopplerReport({ DOPPLER_VARIABLE_NAMES: '' })).toEqual({ pulled: [], failed: [] })
  })
})

describe('formatDopplerReport', () => {
  it('states the counts and both name lists, and never a value', () => {
    const line = formatDopplerReport({
      pulled: ['INTERNAL_API_KEY'],
      failed: [{ name: 'SUPABASE_URL', reason: 'unset' }],
    })

    expect(line).toBe(
      '[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["INTERNAL_API_KEY"] failed=["SUPABASE_URL (unset)"]',
    )
  })
})

describe('logDopplerReport', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('warns when a secret failed, and never logs a value', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const info = vi.spyOn(console, 'info').mockImplementation(() => {})

    logDopplerReport({ DOPPLER_VARIABLE_NAMES: 'A,B', A: 'secret-value-a' })

    expect(info).not.toHaveBeenCalled()
    expect(warn).toHaveBeenCalledOnce()
    const line = String(warn.mock.calls[0][0])
    expect(line).toContain('pulled 1 of 2 secrets, 1 failed')
    expect(line).not.toContain('secret-value-a')
  })

  it('logs at info when every secret arrived', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const info = vi.spyOn(console, 'info').mockImplementation(() => {})

    logDopplerReport({ DOPPLER_VARIABLE_NAMES: 'A', A: 'v' })

    expect(warn).not.toHaveBeenCalled()
    expect(String(info.mock.calls[0][0])).toContain('pulled 1 of 1 secrets, 0 failed')
  })
})
