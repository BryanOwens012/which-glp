"use client"

import { useEffect, useRef } from 'react'
import { HOVER_INTENT_DELAY_MS } from '@/lib/prefetch'

/**
 * Hover-intent prefetching: fires `onHoverIntent(target)` once the pointer
 * has rested on an element for `delayMs` (default 200ms), so quick sweeps
 * across a list don't trigger a prefetch per row.
 *
 * Returns a props getter — spread the result onto each hoverable element:
 *   const getHoverPrefetchProps = useHoverPrefetch((id: string) => prefetch(id))
 *   <div {...getHoverPrefetchProps(row.id)}>…</div>
 */
export const useHoverPrefetch = <T,>(
  onHoverIntent: (target: T) => void,
  delayMs = HOVER_INTENT_DELAY_MS
) => {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Latest-ref pattern: handlers always call the freshest callback without
  // retriggering consumers; assigned in an effect to stay concurrent-safe.
  const onHoverIntentRef = useRef(onHoverIntent)
  useEffect(() => {
    onHoverIntentRef.current = onHoverIntent
  })

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  const getHoverPrefetchProps = (target: T) => ({
    onMouseEnter: () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => onHoverIntentRef.current(target), delayMs)
    },
    onMouseLeave: () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
    },
  })

  return getHoverPrefetchProps
}
