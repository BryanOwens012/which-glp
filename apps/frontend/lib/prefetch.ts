import { SortField, SortDirection, type SortFieldType, type SortDirectionType } from './sort-types'

/**
 * Shared helpers for the app-wide aggressive-prefetching strategy:
 * whenever the user lands anywhere, all other top-level pages (and their
 * queries) are warmed in the background, plus hover-intent and
 * next/previous-page prefetching for lists.
 */

export const EXPERIENCES_PAGE_SIZE = 20

/** Pointer must rest this long on a row/card before its target is prefetched. */
export const HOVER_INTENT_DELAY_MS = 200

/** Fallback delay when requestIdleCallback is unavailable. */
export const IDLE_PREFETCH_TIMEOUT_MS = 1000

/** Distance before the list bottom at which the next page starts fetching. */
export const INFINITE_SCROLL_PREFETCH_ROOT_MARGIN = '1000px 0px'

export type ExperiencesListInput = {
  drug?: string
  search?: string
  sortBy: SortFieldType
  sortOrder: SortDirectionType
  limit: number
}

/**
 * Builds the input for `trpc.experiences.list`. The React Query cache key is
 * derived from this object, so the /experiences page and every prefetcher
 * must build it through this one function — any drift between them means the
 * warmed cache entry is never read.
 */
export const buildExperiencesListInput = (options?: {
  drug?: string
  search?: string
  sortBy?: SortFieldType
  sortOrder?: SortDirectionType
}): ExperiencesListInput => ({
  drug: options?.drug,
  search: options?.search,
  sortBy: options?.sortBy ?? SortField.DATE,
  sortOrder: options?.sortOrder ?? SortDirection.DESC,
  limit: EXPERIENCES_PAGE_SIZE,
})

/**
 * Runs `callback` when the browser is idle so prefetching never competes
 * with rendering the page the user is actually on.
 */
export const runWhenIdle = (callback: () => void, timeoutMs = IDLE_PREFETCH_TIMEOUT_MS): void => {
  if (typeof window === 'undefined') return

  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => callback(), { timeout: timeoutMs })
  } else {
    // Fallback for browsers without requestIdleCallback (e.g. Safari)
    setTimeout(callback, timeoutMs)
  }
}
