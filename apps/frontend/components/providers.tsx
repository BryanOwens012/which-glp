"use client"

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { httpBatchLink } from '@trpc/client'
import { useState } from 'react'
import superjson from 'superjson'
import { trpc } from '@/lib/trpc'
import { TooltipProvider } from '@/components/ui/tooltip'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes - drug data doesn't change frequently
        cacheTime: 10 * 60 * 1000, // 10 minutes - keep in cache longer
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
        httpBatchLink({
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
