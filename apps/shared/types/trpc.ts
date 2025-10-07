/**
 * AppRouter type for tRPC.
 *
 * Re-exports the actual AppRouter type from backend.
 * This works in development where backend is available.
 * For Vercel production builds, TypeScript errors are ignored via next.config.mjs.
 */

export type { AppRouter } from '../../../backend/src/routers/index.js'
