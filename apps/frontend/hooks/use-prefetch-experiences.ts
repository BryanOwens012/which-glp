"use client"

import { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { trpc } from '@/lib/trpc'
import { buildExperiencesListInput } from '@/lib/prefetch'

/**
 * Returns a stable callback that prefetches the /experiences page for a drug
 * — both the route bundle and the warmed list query — so navigating there is
 * instant. Shared by the drug-comparison cards and recommendation results.
 */
export const usePrefetchExperiences = () => {
  const router = useRouter()
  const utils = trpc.useUtils()

  return useCallback(
    ({ drug, search }: { drug: string; search?: string }) => {
      const params = new URLSearchParams({ drug })
      if (search) params.set('search', search)
      router.prefetch(`/experiences?${params.toString()}`)
      // `|| undefined` coerces '' too, matching the page's own input building
      void utils.experiences.list.prefetchInfinite(
        buildExperiencesListInput({ drug, search: search || undefined })
      )
    },
    [router, utils]
  )
}
