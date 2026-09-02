import { afterEach, describe, expect, it } from 'vitest'
import { type ChildProcess, spawn } from 'node:child_process'
import net from 'node:net'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Shutdown behavior can only be observed in a real process: it is about signal
 * handling, the event loop emptying, and the exit code. So these spawn the
 * server rather than importing it.
 *
 * The regression they guard: `server.close()` does not resolve while a request
 * is still in flight, so without a backstop one slow client keeps the process
 * alive until the platform SIGKILLs it — and a SIGKILL runs no cleanup at all.
 * An idle keep-alive connection is NOT enough to reproduce it (Node closes
 * those itself), which is why the second test dribbles a request body.
 */

const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const SERVER_ENTRY = path.join(APP_ROOT, 'src', 'index.ts')
/**
 * Load tsx as an in-process loader rather than running its CLI (directly or via
 * `npx`). Both spawn a wrapper process, and a wrapper does not reliably pass
 * the child's exit code back when signals arrive in quick succession — the
 * double-signal test saw 143 (killed by SIGTERM) instead of the server's own
 * exit code. `--import tsx` keeps it to a single process, so a signal reaches
 * the server's handler and its exit code is the one observed.
 */
const TSX_LOADER_ARGS = ['--import', 'tsx', SERVER_ENTRY]

/** Short enough to keep the suite fast, long enough that a clean exit wins the race. */
const TEST_SHUTDOWN_TIMEOUT_MS = 1_500

/** Ask the OS for a free port, so tests can run in parallel without colliding on one. */
const reservePort = async (): Promise<number> =>
  new Promise((resolve, reject) => {
    const probe = net.createServer()
    probe.on('error', reject)
    probe.listen(0, '127.0.0.1', () => {
      const address = probe.address()

      if (typeof address === 'string' || address === null) {
        probe.close(() => reject(new Error('Could not determine a free port')))
        return
      }

      const { port } = address
      probe.close(() => resolve(port))
    })
  })

type RunningServer = {
  child: ChildProcess
  port: number
  getOutput: () => string
}

const startServer = async (): Promise<RunningServer> => {
  const port = await reservePort()
  let output = ''

  const child = spawn(
    process.execPath,
    TSX_LOADER_ARGS,
    {
      env: {
        ...process.env,
        PORT: String(port),
        NODE_ENV: 'production',
        SHUTDOWN_TIMEOUT_MS: String(TEST_SHUTDOWN_TIMEOUT_MS),
        // Nothing here touches the database; a bad URL only affects procedure
        // results, which these tests never read.
        SUPABASE_URL: 'https://example.supabase.co',
        SUPABASE_SERVICE_KEY: 'test-key',
        // Point at a closed port so the run never depends on a live Redis and
        // never mutates a real one. The service degrades gracefully.
        REDIS_URL: 'redis://127.0.0.1:1',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  )

  child.stdout?.on('data', (chunk) => {
    output += String(chunk)
  })
  child.stderr?.on('data', (chunk) => {
    output += String(chunk)
  })

  const deadline = Date.now() + 30_000

  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`Server exited before becoming ready:\n${output}`)
    }

    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`)

      if (response.ok) {
        return { child, port, getOutput: () => output }
      }
    } catch {
      // Not listening yet.
    }

    await new Promise((resolve) => setTimeout(resolve, 100))
  }

  throw new Error(`Server never became ready:\n${output}`)
}

/** Resolves with the exit code once the process ends. */
const waitForExit = (child: ChildProcess, timeoutMs: number): Promise<number | null> =>
  new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`Process did not exit within ${timeoutMs}ms`))
    }, timeoutMs)

    child.once('exit', (code) => {
      clearTimeout(timer)
      resolve(code)
    })
  })

/**
 * Open a connection, send request headers, then dribble the body — leaving the
 * request in flight, which is what actually holds `server.close()` open.
 */
const openInFlightRequest = (port: number): net.Socket => {
  const socket = net.createConnection({ host: '127.0.0.1', port })

  socket.on('error', () => {
    // The server tearing the connection down is the expected end state here.
  })

  socket.write(
    'POST /trpc/drugs.getAllStats HTTP/1.1\r\n' +
      'Host: localhost\r\n' +
      'Content-Type: application/json\r\n' +
      'Content-Length: 4000\r\n\r\n',
  )

  const dribble = setInterval(() => {
    if (!socket.destroyed) {
      socket.write('a')
    }
  }, 100)

  socket.once('close', () => clearInterval(dribble))

  return socket
}

/** Every spawned process and socket, released after each test on any path. */
const running: RunningServer[] = []
const sockets: net.Socket[] = []

afterEach(() => {
  for (const socket of sockets.splice(0)) {
    socket.destroy()
  }

  for (const { child } of running.splice(0)) {
    if (child.exitCode === null) {
      child.kill('SIGKILL')
    }
  }
})

describe('graceful shutdown', () => {
  it('exits promptly and cleanly on SIGTERM with nothing in flight', async () => {
    const server = await startServer()
    running.push(server)

    server.child.kill('SIGTERM')
    const code = await waitForExit(server.child, 10_000)

    expect(code).toBe(0)
    expect(server.getOutput()).toContain('Shutdown complete')
    // The backstop must not have been what ended it.
    expect(server.getOutput()).not.toContain('Shutdown timed out')
  }, 45_000)

  it('still terminates when a request is in flight, instead of hanging', async () => {
    const server = await startServer()
    running.push(server)

    sockets.push(openInFlightRequest(server.port))
    await new Promise((resolve) => setTimeout(resolve, 500))

    server.child.kill('SIGTERM')

    // Generous relative to the configured backstop: the assertion is that it
    // terminates at all, which it did not before the timeout existed.
    const code = await waitForExit(server.child, 15_000)

    expect(code).toBe(0)
    expect(server.getOutput()).toContain('Shutdown timed out')
  }, 45_000)

  it('runs cleanup once when a second signal arrives', async () => {
    const server = await startServer()
    running.push(server)

    server.child.kill('SIGTERM')
    server.child.kill('SIGINT')

    const code = await waitForExit(server.child, 10_000)
    const shutdownLines = server.getOutput().match(/Shutting down/g) ?? []

    expect(code).toBe(0)
    expect(shutdownLines).toHaveLength(1)
  }, 45_000)
})
