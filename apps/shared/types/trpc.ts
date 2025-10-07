/**
 * Re-export AppRouter type from backend for frontend consumption.
 * This allows type-safe tRPC without importing backend code.
 */
export type { AppRouter } from '../../backend/src/routers/index.js'
