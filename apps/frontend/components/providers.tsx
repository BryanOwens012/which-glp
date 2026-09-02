"use client"

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { httpBatchStreamLink } from '@trpc/client'
import { useState } from 'react'
import superjson from 'superjson'
import { trpc } from '@/lib/trpc'
import { TooltipProvider } from '@/components/ui/tooltip'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes - drug data doesn't change frequently
        gcTime: 10 * 60 * 1000, // 10 minutes - keep in cache longer (React Query v5: renamed from cacheTime)
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        retry: 1, // Only retry once to avoid unnecessary requests
        // Enable structural sharing for better performance
        structuralSharing: true,
      },
      mutations: {
        retry: 1,
      },
    },
  }))

  const [trpcClient] = useState(() =>
    trpc.createClient({
      links: [
        // Streaming, not plain batching. Both collapse same-tick calls into one
        // HTTP request, but httpBatchLink withholds the whole response until its
        // slowest member resolves, so one heavy query stalls every fast query
        // batched beside it. This returns each procedure's result as it
        // resolves, for identical server load.
        //
        // Two things on the API side make that work, and it degrades differently
        // if either is missing: CORS must allow the `trpc-accept` header, or the
        // browser fails every call at preflight; and the server must pipe its
        // response body rather than buffering it, or the stream is reassembled
        // and every result lands at once, gated on the slowest — no failure,
        // just no benefit. Both live in apps/api/src/index.ts.
        httpBatchStreamLink({
          // Fallback matches apps/api's default port (3002) so a fresh clone works without env.
          url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3002/trpc',
          transformer: superjson,
        }),
      ],
    })
  )

  return (
    <trpc.Provider client={trpcClient} queryClient={queryClient}>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider delayDuration={300} skipDelayDuration={100}>
          {children}
        </TooltipProvider>
      </QueryClientProvider>
    </trpc.Provider>
  )
}
