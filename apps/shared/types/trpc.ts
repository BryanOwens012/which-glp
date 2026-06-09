/**
 * AppRouter type for tRPC.
 *
 * Re-exports the inferred AppRouter type from the API service so the frontend
 * tRPC client (`createTRPCReact<AppRouter>()`) is fully typed end-to-end.
 *
 * NOTE: the API lives at `apps/api` (it was previously `backend/`; that stale
 * path silently resolved to `any`, which is why dashboard queries degraded to
 * untyped/implicit-any).
 */

export type { AppRouter } from '../../api/src/routers/index.js'
