/**
 * AppRouter type for tRPC.
 *
 * This creates a minimal type definition that satisfies tRPC without importing backend code.
 */

// Define a minimal procedure type
type AnyProcedure = {
  _type: 'query' | 'mutation' | 'subscription'
  _def: any
}

// Define a router type
type AnyRouter = {
  _def: {
    _config: any
    router: true
    procedures: Record<string, AnyProcedure | AnyRouter>
  }
  createCaller: any
  getErrorShape: any
}

// Create the AppRouter type by extending the base router
export type AppRouter = AnyRouter & {
  platform: AnyRouter
  drugs: AnyRouter
  experiences: AnyRouter
  locations: AnyRouter
  demographics: AnyRouter
}
