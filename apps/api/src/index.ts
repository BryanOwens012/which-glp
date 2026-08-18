import 'dotenv/config'
import { createServer, type IncomingMessage, type ServerResponse } from 'http'
import { Readable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import type { ReadableStream as NodeReadableStream } from 'node:stream/web'
import { fetchRequestHandler } from '@trpc/server/adapters/fetch'
import { resolveClientIp } from './lib/client-ip.js'
import { config } from './lib/config.js'
import { ALLOWED_REQUEST_HEADERS_VALUE, resolveAllowedOrigin } from './lib/cors.js'
import { isHealthRequest, isTrpcRequest } from './lib/routing.js'
import { initPostHog, shutdownPostHog } from './lib/posthog.js'
import {
  blockAddress,
  consumeRateLimit,
  isAddressBlocked,
  type RateLimitDecision,
} from './lib/rate-limit.js'
import { appRouter } from './routers/index.js'

/**
 * Request paths are attacker-controlled strings. Truncate them and strip
 * control characters before they reach a log sink, so a crafted path cannot
 * forge log lines or blow up log volume.
 */
const sanitizePath = (url: string | undefined): string => {
  if (!url) {
    return '(none)'
  }

  return url.replace(/[\x00-\x1f\x7f]/g, '').slice(0, 120)
}

const applyCorsHeaders = (req: IncomingMessage, res: ServerResponse): void => {
  // The response varies by Origin, so any cache in front of this must key on it.
  res.setHeader('Vary', 'Origin')

  const allowedOrigin = resolveAllowedOrigin(req.headers.origin)

  if (!allowedOrigin) {
    return
  }

  res.setHeader('Access-Control-Allow-Origin', allowedOrigin)
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', ALLOWED_REQUEST_HEADERS_VALUE)
  // Cache the preflight so browsers stop re-asking on every batch.
  res.setHeader('Access-Control-Max-Age', '86400')
}

const applyRateLimitHeaders = (res: ServerResponse, decision: RateLimitDecision): void => {
  res.setHeader('RateLimit-Limit', String(decision.limit))
  res.setHeader('RateLimit-Remaining', String(decision.remaining))
}

const sendStatus = (res: ServerResponse, status: number, body: string): void => {
  res.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8' })
  res.end(body)
}

class BodyTooLargeError extends Error {}

/**
 * Read the request body, refusing anything over the configured cap.
 *
 * Both checks are needed: `Content-Length` lets an oversized request be
 * rejected before a byte is buffered, but it is absent under chunked transfer
 * encoding and is in any case client-supplied, so the running total is what
 * actually enforces the limit.
 *
 * @throws BodyTooLargeError when the body exceeds `config.maxRequestBodyBytes`
 */
const readBody = async (req: IncomingMessage): Promise<Buffer> => {
  const declaredLength = Number(req.headers['content-length'])

  if (Number.isFinite(declaredLength) && declaredLength > config.maxRequestBodyBytes) {
    throw new BodyTooLargeError()
  }

  const chunks: Buffer[] = []
  let total = 0

  for await (const chunk of req) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
    total += buffer.length

    if (total > config.maxRequestBodyBytes) {
      // Stop buffering, but do NOT destroy the request here: destroying it
      // resets the socket before the 413 can be written, so the client sees a
      // connection reset it cannot tell apart from a crash. Throwing exits the
      // loop, which stops consuming; Node closes the connection after the
      // response is flushed.
      throw new BodyTooLargeError()
    }

    chunks.push(buffer)
  }

  return Buffer.concat(chunks)
}

/**
 * Apply rate limiting for a request that has already had its client address
 * resolved.
 *
 * @returns true when the request may proceed; false when a response has
 *   already been sent
 */
const enforceRateLimit = async (
  res: ServerResponse,
  ip: string,
  isKnownPath: boolean,
  path: string,
): Promise<boolean> => {
  if (!config.rateLimit.isEnabled) {
    return true
  }

  // A block is deliberately scoped to unknown paths. Carrier-grade NAT and
  // office networks put many unrelated clients behind one address, so blocking
  // the whole API would let a single compromised host lock real users out of
  // the site. Probes stay cheap to refuse, and genuine /trpc traffic from that
  // address still answers to its own (independent) budget.
  if (!isKnownPath && (await isAddressBlocked(ip))) {
    res.setHeader('Retry-After', String(config.rateLimit.unknownPath.blockSeconds))
    sendStatus(res, 429, 'Too Many Requests')
    return false
  }

  const decision = await consumeRateLimit(ip, isKnownPath ? 'api' : 'unknownPath')
  applyRateLimitHeaders(res, decision)

  if (decision.isAllowed) {
    return true
  }

  // Exhausting the unknown-path budget means this address is walking paths the
  // service does not serve — a scanner. Block it rather than answering each probe.
  if (!isKnownPath) {
    await blockAddress(ip, config.rateLimit.unknownPath.blockSeconds)
    console.warn(
      `🚫 Blocked ${ip} for ${config.rateLimit.unknownPath.blockSeconds}s after ` +
        `${decision.limit} unknown-path requests (most recent: ${path})`,
    )
  }

  res.setHeader('Retry-After', String(decision.retryAfterSeconds))
  sendStatus(res, 429, 'Too Many Requests')
  return false
}

const handleRequest = async (req: IncomingMessage, res: ServerResponse): Promise<void> => {
  applyCorsHeaders(req, res)

  // Answer preflight before any budget is consumed: a preflight is the browser's
  // own overhead for a request that has not happened yet, so charging for both
  // would halve every real client's usable budget.
  if (req.method === 'OPTIONS') {
    res.writeHead(204)
    res.end()
    return
  }

  const path = sanitizePath(req.url)
  const isTrpcPath = isTrpcRequest(req.url)
  const isHealthPath = isHealthRequest(req.url)
  // Paths this service actually serves draw on the API budget; everything else
  // draws on the far tighter unknown-path budget.
  const isKnownPath = isTrpcPath || isHealthPath
  const ip = resolveClientIp(req)

  if (!ip) {
    // No usable client address means no way to hold this caller to a budget.
    // Refuse rather than granting an unmetered lane (fail closed).
    console.warn(`⚠️  Refusing request with unresolvable client address: ${path}`)
    sendStatus(res, 400, 'Bad Request')
    return
  }

  if (!(await enforceRateLimit(res, ip, isKnownPath, path))) {
    return
  }

  // Answered before the /trpc check so uptime monitors have a stable, cheap
  // endpoint that does not consume the unknown-path budget and get blocked.
  if (isHealthPath) {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify({ status: 'ok', service: 'api' }))
    return
  }

  if (!isTrpcPath) {
    // Deliberately not logged per-request at info: unknown paths are almost
    // entirely scanner noise, and logging each one turns a single spray into
    // hundreds of billable log lines. The block above is what gets logged.
    sendStatus(res, 404, 'Not Found')
    return
  }

  console.log(`${req.method} ${path}`)

  let body: Buffer

  try {
    body = await readBody(req)
  } catch (error) {
    if (error instanceof BodyTooLargeError) {
      console.warn(`⚠️  Rejected oversized request body from ${ip} on ${path}`)
      sendStatus(res, 413, 'Payload Too Large')
      return
    }

    throw error
  }

  const request = new Request(`http://${req.headers.host}${req.url}`, {
    method: req.method,
    headers: Object.entries(req.headers).reduce((acc, [key, value]) => {
      if (value) acc[key] = Array.isArray(value) ? value.join(', ') : value
      return acc
    }, {} as Record<string, string>),
    // The cap above is enforced on raw bytes (the only honest measure); tRPC
    // itself speaks JSON, so the body is handed over decoded as UTF-8.
    body: body.length > 0 ? body.toString('utf8') : undefined,
  })

  const response = await fetchRequestHandler({
    endpoint: '/trpc',
    req: request,
    router: appRouter,
    createContext: () => ({}),
  })

  // tRPC sets its own content type; CORS headers set above are preserved because
  // writeHead merges with headers already set on the response.
  res.writeHead(response.status, Object.fromEntries(response.headers.entries()))

  if (!response.body) {
    res.end()
    return
  }

  // Pipe the body through rather than buffering it. Awaiting `arrayBuffer()`
  // here would drain the whole stream before writing a byte, which silently
  // undoes streaming: every procedure in a batch would land at once, gated on
  // the slowest, exactly as if the client had never asked to stream.
  //
  // `pipeline` (not `.pipe()`) so a client that disconnects mid-response
  // destroys both ends instead of leaving the source stream dangling.
  // The cast bridges two declarations of the same runtime object: fetch's body
  // is typed with the DOM lib's ReadableStream, while Readable.fromWeb expects
  // the node:stream/web one. They are the same stream at runtime.
  await pipeline(Readable.fromWeb(response.body as NodeReadableStream<Uint8Array>), res)
}

const handleRequestSafely = (req: IncomingMessage, res: ServerResponse): void => {
  // The handler is async, so nothing inside it can reject into `createServer`'s
  // synchronous frame. Without this catch an unexpected throw becomes an
  // unhandled rejection and the request hangs until the client times out.
  handleRequest(req, res).catch((error) => {
    console.error('❌ Unhandled request error:', error)

    if (!res.headersSent) {
      sendStatus(res, 500, 'Internal Server Error')
      return
    }

    res.end()
  })
}

const server = createServer(handleRequestSafely)

/**
 * Reject an oversized upload at the `Expect: 100-continue` handshake.
 *
 * Clients sending a large body ask permission first. Answering 413 here means
 * the body is never transmitted at all — the cheapest possible rejection, for
 * us and for the client. Registering this listener disables Node's automatic
 * `100 Continue`, so the accept path must send it explicitly.
 */
server.on('checkContinue', (req, res) => {
  const declaredLength = Number(req.headers['content-length'])

  if (Number.isFinite(declaredLength) && declaredLength > config.maxRequestBodyBytes) {
    sendStatus(res, 413, 'Payload Too Large')
    return
  }

  res.writeContinue()
  handleRequestSafely(req, res)
})

initPostHog()

server.listen(config.port)
console.log(`✅ tRPC server running on http://localhost:${config.port}`)
console.log(
  `🛡️  Rate limiting ${config.rateLimit.isEnabled ? 'enabled' : 'DISABLED'} — ` +
    `api ${config.rateLimit.api.maxRequests}/${config.rateLimit.api.windowSeconds}s, ` +
    `unknown-path ${config.rateLimit.unknownPath.maxRequests}/${config.rateLimit.unknownPath.windowSeconds}s`,
)

// Graceful shutdown
const shutdown = async () => {
  console.log('\n🔄 Shutting down...')
  server.close(async () => {
    await shutdownPostHog()
    process.exit(0)
  })
}

process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)
