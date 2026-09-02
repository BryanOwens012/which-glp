/**
 * Bridge from a fetch-style `Response` (what tRPC's fetch adapter returns) to
 * Node's `ServerResponse`.
 *
 * The body is piped, never buffered. Awaiting `response.arrayBuffer()` would
 * drain the whole stream before writing a byte, which silently undoes
 * `httpBatchStreamLink`: every procedure in a batch would land at once, gated
 * on the slowest, with nothing failing to say so.
 */

import type { ServerResponse } from 'node:http'
import { Readable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import type { ReadableStream as NodeReadableStream } from 'node:stream/web'

/** Error codes Node raises when the client goes away before the response is fully written. */
const CLIENT_DISCONNECT_CODES = ['ERR_STREAM_PREMATURE_CLOSE', 'ECONNRESET', 'EPIPE'] as const

/**
 * Whether an error means the client disconnected mid-response. That is not a
 * server fault: nothing can be sent and nothing needs logging as an error.
 */
export const isClientDisconnect = (error: unknown): boolean =>
  error instanceof Error &&
  CLIENT_DISCONNECT_CODES.includes(
    (error as NodeJS.ErrnoException).code as (typeof CLIENT_DISCONNECT_CODES)[number],
  )

/**
 * Write `response` to `res`: status and headers first, then the body as it
 * arrives.
 *
 * `pipeline` (not `.pipe()`) so a client that disconnects mid-response
 * destroys both ends instead of leaving the source stream dangling; in that
 * case this rejects with a client-disconnect error (see `isClientDisconnect`).
 * A body-less response (204) ends normally.
 */
export const writeFetchResponse = async (res: ServerResponse, response: Response): Promise<void> => {
  // Headers set on `res` beforehand (CORS, rate limit) survive: writeHead merges.
  res.writeHead(response.status, Object.fromEntries(response.headers.entries()))

  if (!response.body) {
    res.end()
    return
  }

  // The cast bridges two declarations of the same runtime object: fetch's body
  // is typed with the DOM lib's ReadableStream, while Readable.fromWeb expects
  // the node:stream/web one.
  await pipeline(Readable.fromWeb(response.body as NodeReadableStream<Uint8Array>), res)
}
