/**
 * Entry point: load this service's secrets, then start the server.
 *
 * Static imports run before any statement in a module, and several server modules
 * read secrets at import time (`supabase.ts` throws on a missing key). So the
 * server is imported dynamically, only after the Doppler load has populated
 * `process.env`.
 */
// Must stay the first import: masks Supabase secret keys before any other module runs.
import './lib/install-redaction.js'
import 'dotenv/config'
import { loadDopplerSecrets } from './lib/doppler-secrets.js'

/** The secrets this service reads; nothing else is requested from Doppler. */
const DOPPLER_SECRETS = [
  'INTERNAL_API_KEY',
  'POSTHOG_API_KEY',
  'POSTHOG_HOST',
  'SUPABASE_SECRET_KEY',
  'SUPABASE_URL',
] as const

await loadDopplerSecrets(DOPPLER_SECRETS)
await import('./server.js')
