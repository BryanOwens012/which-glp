import { describe, expect, it } from 'vitest'
import { parseSupabaseSecretKey } from './config.js'

describe('parseSupabaseSecretKey', () => {
  it('accepts a Supabase secret key', () => {
    expect(parseSupabaseSecretKey('sb_secret_abc123')).toBe('sb_secret_abc123')
  })

  it.each([undefined, ''])('rejects a missing key (%j)', (raw) => {
    expect(() => parseSupabaseSecretKey(raw)).toThrow('Missing SUPABASE_SECRET_KEY')
  })

  it.each([
    ['a publishable key', 'sb_publishable_abc123'],
    ['a legacy service_role JWT', 'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.sig'],
    ['a value with leading whitespace', ' sb_secret_abc123'],
    ['a value with a trailing CR', 'sb_secret_abc123\r'],
    ['a value with inner whitespace', 'sb_secret_abc 123'],
    ['the bare prefix', 'sb_secret_'],
  ])('rejects %s', (_label, raw) => {
    expect(() => parseSupabaseSecretKey(raw)).toThrow('Invalid SUPABASE_SECRET_KEY')
  })
})
