import { describe, expect, it } from 'vitest'
import type { ServerResponse } from 'node:http'
import { Writable } from 'node:stream'
import { isClientDisconnect, writeFetchResponse } from './http-response.js'

type Head = { status: number; headers: Record<string, string> }

/**
 * A Writable that records what reaches it, with the one ServerResponse method
 * the helper calls. Chunks are captured in arrival order, which is the whole
 * point: the streaming guarantee is about *when* bytes are written.
 */
const makeSink = () => {
  const chunks: string[] = []
  let head: Head | null = null

  const sink = new Writable({
    write(chunk, _encoding, callback) {
      chunks.push(String(chunk))
      callback()
    },
  })

  Object.assign(sink, {
    writeHead: (status: number, headers: Record<string, string>) => {
      head = { status, headers }
      return sink
    },
  })

  return {
    res: sink as unknown as ServerResponse,
    sink,
    chunks,
    getHead: () => head,
  }
}

const encode = (text: string): Uint8Array => new TextEncoder().encode(text)

const waitFor = async (isDone: () => boolean, timeoutMs: number): Promise<void> => {
  const deadline = Date.now() + timeoutMs

  while (!isDone() && Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 10))
  }
}

describe('writeFetchResponse', () => {
  it('writes each chunk as the body produces it, without waiting for the end', async () => {
    // The second chunk is held behind a gate the test controls. Piping writes
    // the first chunk while the gate is still closed; buffering cannot, since
    // it waits for the stream to end, which only happens after the gate opens.
    let openGate: () => void = () => {}
    const gate = new Promise<void>((resolve) => {
      openGate = resolve
    })

    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        controller.enqueue(encode('first\n'))
        await gate
        controller.enqueue(encode('second\n'))
        controller.close()
      },
    })

    const { res, chunks, getHead } = makeSink()
    const done = writeFetchResponse(res, new Response(body, { status: 200 }))

    await waitFor(() => chunks.length > 0, 1_000)
    const writtenBeforeGateOpened = [...chunks]

    openGate()
    await done

    expect(writtenBeforeGateOpened).toEqual(['first\n'])
    expect(chunks).toEqual(['first\n', 'second\n'])
    expect(getHead()?.status).toBe(200)
  })

  it('forwards status and headers before the body', async () => {
    const { res, chunks, getHead } = makeSink()

    await writeFetchResponse(
      res,
      new Response('{"ok":true}', {
        status: 201,
        headers: { 'content-type': 'application/json' },
      }),
    )

    expect(getHead()).toEqual({ status: 201, headers: { 'content-type': 'application/json' } })
    expect(chunks.join('')).toBe('{"ok":true}')
  })

  it('ends a body-less response', async () => {
    const { res, sink, chunks, getHead } = makeSink()

    await writeFetchResponse(res, new Response(null, { status: 204 }))

    expect(getHead()?.status).toBe(204)
    expect(chunks).toEqual([])
    expect(sink.writableEnded).toBe(true)
  })

  it('rejects with a client-disconnect error when the sink is destroyed mid-body', async () => {
    let openGate: () => void = () => {}
    const gate = new Promise<void>((resolve) => {
      openGate = resolve
    })

    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        controller.enqueue(encode('first\n'))
        await gate
        controller.enqueue(encode('second\n'))
        controller.close()
      },
    })

    const { res, sink, chunks } = makeSink()
    const done = writeFetchResponse(res, new Response(body, { status: 200 }))

    await waitFor(() => chunks.length > 0, 1_000)
    sink.destroy()
    openGate()

    await expect(done).rejects.toSatisfy(isClientDisconnect)
  })
})

describe('isClientDisconnect', () => {
  it('recognizes the codes Node raises when the client goes away', () => {
    for (const code of ['ERR_STREAM_PREMATURE_CLOSE', 'ECONNRESET', 'EPIPE']) {
      expect(isClientDisconnect(Object.assign(new Error(code), { code }))).toBe(true)
    }
  })

  it('does not swallow other errors', () => {
    expect(isClientDisconnect(new Error('boom'))).toBe(false)
    expect(isClientDisconnect(Object.assign(new Error('x'), { code: 'ENOENT' }))).toBe(false)
    expect(isClientDisconnect('ECONNRESET')).toBe(false)
    expect(isClientDisconnect(undefined)).toBe(false)
  })
})
