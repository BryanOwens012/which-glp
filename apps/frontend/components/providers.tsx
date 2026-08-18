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
        // Requires the API to allow the `trpc-accept` header in CORS, which it
        // must already be deployed doing — see the note in the PR.
        httpBatchStreamLink({
          url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/trpc',
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
