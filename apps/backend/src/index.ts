import 'dotenv/config'
import { createServer } from 'http'
import { fetchRequestHandler } from '@trpc/server/adapters/fetch'
import { appRouter } from './routers/index.js'

const PORT = process.env.PORT || 3002

const server = createServer(async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin || '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  res.setHeader('Access-Control-Allow-Credentials', 'true')

  // Handle preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204)
    res.end()
    return
  }

  // Log all requests
  console.log(`${req.method} ${req.url}`)

  // Only handle /trpc path
  if (!req.url?.startsWith('/trpc')) {
    console.log(`  ❌ Not a /trpc path, returning 404`)
    res.writeHead(404)
    res.end('Not Found')
    return
  }

  // Create a Web Request from Node request
  const url = `http://${req.headers.host}${req.url}`

  let body = ''
  for await (const chunk of req) {
    body += chunk
  }

  const request = new Request(url, {
    method: req.method,
    headers: Object.entries(req.headers).reduce((acc, [key, value]) => {
      if (value) acc[key] = Array.isArray(value) ? value.join(', ') : value
      return acc
    }, {} as Record<string, string>),
    body: body || undefined,
  })

  // Handle with tRPC
  const response = await fetchRequestHandler({
    endpoint: '/trpc',
    req: request,
    router: appRouter,
    createContext: () => ({}),
  })

  // Send response
  res.writeHead(response.status, Object.fromEntries(response.headers.entries()))
  res.end(await response.text())
})

server.listen(PORT)
console.log(`✅ tRPC server running on http://localhost:${PORT}`)
