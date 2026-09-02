/**
 * CORS origin allowlist.
 *
 * Reflecting whatever arrives in the `Origin` header — especially alongside
 * `Access-Control-Allow-Credentials: true` — lets any site on the internet make
 * credentialed cross-origin calls and read the response. This module resolves
 * an origin against an explicit allowlist instead and fails closed: an origin
 * it does not recognize gets no CORS header at all, so the browser blocks the
 * read.
 */

import { config } from './config.js'

/**
 * Resolve the value for `Access-Control-Allow-Origin`.
 *
 * @param origin - the request's `Origin` header, if any
 * @returns the origin to echo back, or `null` when it is not allowed
 *
 * A request with no `Origin` header (server-to-server, curl, same-origin
 * navigation) returns `null`: CORS headers exist to grant a *browser* cross-origin
 * read permission, and a request without an origin needs none.
 */
export const resolveAllowedOrigin = (origin: string | undefined): string | null => {
  if (!origin) {
    return null
  }

  if (config.cors.allowedOrigins.has(origin)) {
    return origin
  }

  if (
    config.cors.arePreviewOriginsAllowed &&
    config.cors.previewOriginPattern.test(origin)
  ) {
    return origin
  }

  return null
}
