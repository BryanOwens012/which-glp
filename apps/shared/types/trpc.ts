/**
 * AppRouter type for tRPC.
 *
 * For Vercel builds, we cannot import from backend due to missing dependencies.
 * We use `any` as a workaround to avoid importing backend code during frontend builds.
 *
 * Type safety is maintained in development where the full backend types are available.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AppRouter = any
