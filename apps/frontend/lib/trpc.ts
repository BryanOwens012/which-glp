import { createTRPCReact } from '@trpc/react-query'
import type { AppRouter } from '../../shared/types/trpc'

// Create tRPC React hooks
export const trpc = createTRPCReact<AppRouter>()
