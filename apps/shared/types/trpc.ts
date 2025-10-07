/**
 * Re-export AppRouter type from backend for frontend consumption.
 *
 * The frontend now has @supabase/supabase-js as a devDependency,
 * so TypeScript can resolve backend imports during build.
 */
export type { AppRouter } from '../../backend/src/routers/index.js'
