import { describe, expect, it } from 'vitest'
import { parseInternalApiKey, parseSupabaseSecretKey } from './config.js'

describe('parseSupabaseSecretKey', () => {
  it.each(['sb_secret_abc123', 'sb_secret_ab.c+d/e='])('accepts a Supabase secret key (%s)', (raw) => {
    expect(parseSupabaseSecretKey(raw)).toBe(raw)
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
    ['a value with an inner tab', 'sb_secret_abc\t123'],
  ])('rejects %s', (_label, raw) => {
    expect(() => parseSupabaseSecretKey(raw)).toThrow('Invalid SUPABASE_SECRET_KEY')
  })
})

describe('parseInternalApiKey', () => {
  it('accepts a key with no whitespace', () => {
    expect(parseInternalApiKey('k3y-Value_123')).toBe('k3y-Value_123')
  })

  it.each([
    ['missing', undefined, 'Missing INTERNAL_API_KEY'],
    ['empty', '', 'Missing INTERNAL_API_KEY'],
    ['a trailing newline', 'abc\n', 'printable ASCII'],
    ['a carriage return', 'abc\r', 'printable ASCII'],
    ['an inner space', 'ab c', 'printable ASCII'],
    ['a tab', 'ab\tc', 'printable ASCII'],
    ['a byte-order mark', '\ufeffabc', 'printable ASCII'],
    ['a control character', 'ab\x1cc', 'printable ASCII'],
    ['non-ASCII', 'abé', 'printable ASCII'],
    ['DEL', 'ab\x7fc', 'printable ASCII'],
  ])('refuses a key that is %s', (_label, raw, message) => {
    expect(() => parseInternalApiKey(raw)).toThrow(message)
  })
})
