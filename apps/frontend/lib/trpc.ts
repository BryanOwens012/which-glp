import { createTRPCReact } from '@trpc/react-query'
import type { AppRouter } from '@backend/routers'

// Create tRPC React hooks
export const trpc = createTRPCReact<AppRouter>()
