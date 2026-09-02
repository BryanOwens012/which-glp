import { describe, expect, it } from 'vitest'
import {
  ALLOWED_REQUEST_HEADERS,
  ALLOWED_REQUEST_HEADERS_VALUE,
  resolveAllowedOrigin,
} from './cors.js'

describe('resolveAllowedOrigin', () => {
  it('allows the production origins', () => {
    expect(resolveAllowedOrigin('https://www.whichglp.com')).toBe('https://www.whichglp.com')
    expect(resolveAllowedOrigin('https://whichglp.com')).toBe('https://whichglp.com')
  })

  it('allows a Vercel preview deployment for this project', () => {
    const preview = 'https://which-glp-git-bryan-feature-bryanowens012s-projects.vercel.app'

    expect(resolveAllowedOrigin(preview)).toBe(preview)
  })

  it('refuses an unrelated origin', () => {
    expect(resolveAllowedOrigin('https://evil.example.com')).toBeNull()
  })

  it('refuses a lookalike that merely contains an allowed host', () => {
    // The failure mode an unanchored pattern would introduce: the allowed host
    // appears in the string, but the actual origin belongs to someone else.
    expect(resolveAllowedOrigin('https://which-glp-evil.vercel.app.attacker.com')).toBeNull()
    expect(resolveAllowedOrigin('https://www.whichglp.com.attacker.com')).toBeNull()
    expect(resolveAllowedOrigin('https://notwhichglp.com')).toBeNull()
  })

  it('refuses a preview origin belonging to a different project', () => {
    expect(resolveAllowedOrigin('https://other-project-abc123.vercel.app')).toBeNull()
  })

  it('refuses the plaintext scheme for an otherwise allowed host', () => {
    expect(resolveAllowedOrigin('http://www.whichglp.com')).toBeNull()
  })

  it('returns null when no Origin header was sent', () => {
    // Not an error: a request without an Origin needs no CORS grant.
    expect(resolveAllowedOrigin(undefined)).toBeNull()
    expect(resolveAllowedOrigin('')).toBeNull()
  })

  it('refuses the wildcard and the literal "null" origin', () => {
    expect(resolveAllowedOrigin('*')).toBeNull()
    // Sandboxed iframes and some redirects send Origin: null.
    expect(resolveAllowedOrigin('null')).toBeNull()
  })
})

describe('allowed request headers', () => {
  it('permits trpc-accept, which httpBatchStreamLink sends', () => {
    // Without this the browser refuses every tRPC call at preflight, because
    // trpc-accept is not CORS-safelisted.
    expect(ALLOWED_REQUEST_HEADERS).toContain('trpc-accept')
  })

  it('still permits the headers ordinary requests rely on', () => {
    expect(ALLOWED_REQUEST_HEADERS).toContain('Content-Type')
    expect(ALLOWED_REQUEST_HEADERS).toContain('Authorization')
  })

  it('renders every allowed header into the comma-separated header value', () => {
    // Asserted on the rendering contract rather than a pinned literal: this
    // still catches a wrong separator (which browsers would fail to parse)
    // without breaking the day someone adds a header to the list.
    expect(ALLOWED_REQUEST_HEADERS_VALUE.split(', ')).toEqual([...ALLOWED_REQUEST_HEADERS])
  })
})
