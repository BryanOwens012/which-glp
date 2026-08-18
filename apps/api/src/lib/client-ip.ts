/**
 * Client IP resolution for requests arriving through Railway's edge proxy.
 *
 * Rate limiting is only as good as the identity it counts against, so this
 * deliberately picks the one entry in the chain an attacker cannot forge.
 */

import type { IncomingMessage } from 'node:http'

/** `1.2.3.4:5678` — an IPv4 address with a port suffix. */
const IPV4_WITH_PORT = /^(\d{1,3}(?:\.\d{1,3}){3}):\d+$/
/** `[2001:db8::1]:5678` — a bracketed IPv6 address, with or without a port. */
const IPV6_BRACKETED = /^\[([^\]]+)\](?::\d+)?$/
/** IPv4-mapped IPv6, e.g. `::ffff:1.2.3.4`. */
const IPV4_MAPPED_IPV6 = /^::ffff:(\d{1,3}(?:\.\d{1,3}){3})$/i

const IPV4 = /^\d{1,3}(?:\.\d{1,3}){3}$/

/**
 * Strip a port and any IPv6 bracketing, and collapse IPv4-mapped IPv6 to plain
 * IPv4 so one client cannot occupy two rate-limit buckets by switching form.
 */
const normalizeAddress = (raw: string): string | null => {
  const trimmed = raw.trim()

  if (trimmed === '') {
    return null
  }

  const bracketed = IPV6_BRACKETED.exec(trimmed)
  const unbracketed = bracketed ? bracketed[1] : trimmed

  const withPort = IPV4_WITH_PORT.exec(unbracketed)
  const withoutPort = withPort ? withPort[1] : unbracketed

  const mapped = IPV4_MAPPED_IPV6.exec(withoutPort)
  const address = mapped ? mapped[1] : withoutPort

  if (address === '') {
    return null
  }

  // An IPv4 address whose octets are out of range is not an address at all —
  // treat it as unusable rather than counting it as a distinct client.
  if (IPV4.test(address)) {
    const isInRange = address
      .split('.')
      .every((octet) => Number(octet) <= 255)

    return isInRange ? address : null
  }

  // Anything else must at least look like IPv6 (hex groups and colons).
  return /^[0-9a-f:]+$/i.test(address) ? address.toLowerCase() : null
}

/**
 * Resolve the client IP for a request.
 *
 * `X-Forwarded-For` is a chain — `client, proxy1, proxy2` — where each proxy
 * appends the address it received the request FROM. A client can therefore put
 * anything it likes at the head of the chain, so the leftmost entry is
 * attacker-controlled and must never be used for rate limiting.
 *
 * The **rightmost** entry is the one appended by the last proxy the request
 * passed through — Railway's edge — and is the address Railway actually
 * observed. That is the only entry an attacker cannot forge, so it is the one
 * used here.
 *
 * @param req - the incoming Node request
 * @returns the normalized client address, or `null` when none can be
 *   determined (callers must decide how to treat an unidentifiable client)
 */
export const resolveClientIp = (req: IncomingMessage): string | null => {
  const forwardedFor = req.headers['x-forwarded-for']

  const chain = Array.isArray(forwardedFor)
    ? forwardedFor.join(',')
    : (forwardedFor ?? '')

  const entries = chain
    .split(',')
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0)

  for (let index = entries.length - 1; index >= 0; index -= 1) {
    const normalized = normalizeAddress(entries[index])

    if (normalized) {
      return normalized
    }
  }

  return req.socket.remoteAddress ? normalizeAddress(req.socket.remoteAddress) : null
}
