/**
 * AppRouter type for tRPC.
 *
 * For Vercel builds, we cannot import from backend due to missing dependencies.
 * Instead, we define a compatible stub type that satisfies tRPC's requirements.
 */

import type { RootConfig } from '@trpc/server'

// Define a minimal router structure that tRPC can work with
type ProcedureRouterRecord = Record<string, any>

export interface AppRouter extends RootConfig<{
  ctx: object
  meta: object
  errorShape: any
  transformer: any
}> {
  _def: {
    _config: any
    router: true
    procedures: ProcedureRouterRecord
  }
  createCaller: any
  getErrorShape: any
  platform: any
  drugs: any
  experiences: any
  locations: any
  demographics: any
}
