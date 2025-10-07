/**
 * AppRouter type for tRPC.
 *
 * This creates a minimal type definition that satisfies tRPC without importing backend code.
 */

import type { inferRouterInputs, inferRouterOutputs } from '@trpc/server'

// Define the router structure as an interface
export interface AppRouter {
  _def: {
    _config: {
      transformer: {
        input: { serialize: (obj: any) => any; deserialize: (obj: any) => any }
        output: { serialize: (obj: any) => any; deserialize: (obj: any) => any }
      }
      errorFormatter: any
      allowOutsideOfServer: boolean
      isServer: boolean
      $types: any
    }
    router: true
    procedures: {
      platform: any
      drugs: any
      experiences: any
      locations: any
      demographics: any
    }
  }
}
