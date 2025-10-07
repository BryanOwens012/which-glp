/**
 * AppRouter type for tRPC.
 *
 * For Vercel builds, we cannot import from backend due to missing dependencies.
 * Instead, we define a compatible stub type that satisfies tRPC's requirements.
 */

// Create a minimal procedure type that tRPC can work with
type AnyProcedure = {
  _def: any
  [key: string]: any
}

// Define router record with nested routers
type RouterRecord = {
  [key: string]: AnyProcedure | RouterRecord
}

// Main AppRouter type compatible with tRPC
export type AppRouter = {
  _def: {
    _config: {
      transformer: any
      errorFormatter: any
      allowOutsideOfServer: boolean
      isServer: boolean
      isDev: boolean
    }
    router: true
    procedures: RouterRecord
    record: RouterRecord
    queries: RouterRecord
    mutations: RouterRecord
    subscriptions: RouterRecord
  }
  createCaller: (ctx: any) => any
  getErrorShape: (opts: any) => any

  // Define the actual router structure
  platform: {
    getStats: AnyProcedure
    [key: string]: any
  }
  drugs: {
    list: AnyProcedure
    getById: AnyProcedure
    [key: string]: any
  }
  experiences: {
    list: AnyProcedure
    getById: AnyProcedure
    [key: string]: any
  }
  locations: {
    list: AnyProcedure
    [key: string]: any
  }
  demographics: {
    getStats: AnyProcedure
    [key: string]: any
  }
}
