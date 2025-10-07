import { initTRPC } from '@trpc/server'
import superjson from 'superjson'

// Initialize tRPC
const t = initTRPC.create({
  transformer: superjson,
})

export const router = t.router
export const publicProcedure = t.procedure
