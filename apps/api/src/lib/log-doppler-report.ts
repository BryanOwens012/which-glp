/**
 * Side-effect module: imported by `index.ts` right after `dotenv/config`, so the
 * Doppler secrets report prints before any module that reads a secret at import
 * time (`supabase.ts` throws on a missing key) can stop the boot.
 */
import { logDopplerReport } from './doppler-report.js'

logDopplerReport()
