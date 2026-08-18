import { describe, expect, it } from 'vitest'
import type { IncomingMessage } from 'node:http'
import { resolveClientIp } from './client-ip.js'

/** Minimal IncomingMessage stand-in — resolveClientIp only reads headers + socket. */
const makeRequest = (
  headers: Record<string, string | string[] | undefined>,
  remoteAddress?: string,
): IncomingMessage =>
  ({
    headers,
    socket: { remoteAddress },
  }) as unknown as IncomingMessage

describe('resolveClientIp', () => {
  it('uses the socket address when no forwarding header is present', () => {
    expect(resolveClientIp(makeRequest({}, '203.0.113.9'))).toBe('203.0.113.9')
  })

  it('takes the rightmost forwarded entry, which the proxy appended', () => {
    const req = makeRequest(
      { 'x-forwarded-for': '198.51.100.1, 203.0.113.7' },
      '10.0.0.1',
    )

    expect(resolveClientIp(req)).toBe('203.0.113.7')
  })

  it('ignores a spoofed leftmost entry supplied by the client', () => {
    // A client sending its own X-Forwarded-For gets that value pushed left as
    // the edge appends the address it actually observed. Trusting the left
    // entry would let any caller pick its own rate-limit bucket.
    const req = makeRequest(
      { 'x-forwarded-for': '1.2.3.4, 203.0.113.7' },
      '10.0.0.1',
    )

    expect(resolveClientIp(req)).not.toBe('1.2.3.4')
    expect(resolveClientIp(req)).toBe('203.0.113.7')
  })

  it('joins a repeated header into one chain and still takes the rightmost', () => {
    const req = makeRequest(
      { 'x-forwarded-for': ['1.2.3.4', '203.0.113.7'] },
      '10.0.0.1',
    )

    expect(resolveClientIp(req)).toBe('203.0.113.7')
  })

  it('strips a port from an IPv4 address', () => {
    expect(resolveClientIp(makeRequest({}, '203.0.113.9:54321'))).toBe('203.0.113.9')
  })

  it('unwraps a bracketed IPv6 address with a port', () => {
    expect(resolveClientIp(makeRequest({}, '[2001:db8::1]:443'))).toBe('2001:db8::1')
  })

  it('collapses IPv4-mapped IPv6 so one client cannot occupy two buckets', () => {
    const mapped = resolveClientIp(makeRequest({}, '::ffff:203.0.113.9'))
    const plain = resolveClientIp(makeRequest({}, '203.0.113.9'))

    expect(mapped).toBe('203.0.113.9')
    expect(mapped).toBe(plain)
  })

  it('falls back past unusable forwarded entries', () => {
    const req = makeRequest(
      { 'x-forwarded-for': '203.0.113.7, not-an-address' },
      '10.0.0.1',
    )

    expect(resolveClientIp(req)).toBe('203.0.113.7')
  })

  it('rejects an IPv4 address with an out-of-range octet', () => {
    expect(resolveClientIp(makeRequest({}, '999.1.1.1'))).toBeNull()
  })

  it('returns null when no address can be determined', () => {
    expect(resolveClientIp(makeRequest({ 'x-forwarded-for': '  ,  ' }))).toBeNull()
    expect(resolveClientIp(makeRequest({}))).toBeNull()
  })
})
