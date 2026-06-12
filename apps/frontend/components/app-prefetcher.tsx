"use client"

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { trpc } from '@/lib/trpc'
import { buildExperiencesListInput, runWhenIdle } from '@/lib/prefetch'

const topLevelRoutes = [
  '/',
  '/experiences',
  '/recommendations',
  '/dashboard',
  '/about',
  '/privacy',
  '/terms',
] as const

/**
 * Mounted once in the root layout. Whenever the user lands on any page, it
 * prefetches every other top-level page — both the route bundle and the
 * underlying tRPC queries (which also covers every dashboard tab, since the
 * dashboard fetches all of its tabs' queries up front). Everything runs
 * during browser idle time so it never competes with the current page, and
 * the QueryClient's staleTime makes repeat prefetches free.
 */
export const AppPrefetcher = () => {
  const pathname = usePathname()
  const router = useRouter()
  const utils = trpc.useUtils()

  useEffect(() => {
    runWhenIdle(() => {
      // Frontend: route bundles for all other top-level pages
      for (const route of topLevelRoutes) {
        if (route !== pathname) router.prefetch(route)
      }

      // Data: warm the queries behind every top-level page and tab
      void utils.platform.getStats.prefetch() // home + dashboard
      void utils.drugs.getAllStats.prefetch() // home comparison tabs + experiences filter + dashboard
      void utils.experiences.list.prefetchInfinite(buildExperiencesListInput()) // experiences default view
      void utils.locations.getData.prefetch() // dashboard "Cost by Location" tab
      void utils.demographics.getData.prefetch() // dashboard "Demographics" tab
      void utils.platform.getTrends.prefetch({ period: 'month' }) // dashboard "Trends" tab
    })
  }, [pathname, router, utils])

  return null
}
