"use client"

import { useEffect, useState } from 'react'

/** How long a load must run before loading UI may appear (avoids flashes). */
export const LOADING_INDICATOR_DELAY_MS = 200

/**
 * Returns true only after `isActive` has been true for `delayMs`, so loading
 * UI never flashes for fast operations. Resets immediately when `isActive`
 * goes false.
 */
export const useDelayedVisible = (
  isActive: boolean,
  delayMs = LOADING_INDICATOR_DELAY_MS
): boolean => {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (!isActive) {
      setIsVisible(false)
      return
    }
    const timer = setTimeout(() => setIsVisible(true), delayMs)
    return () => clearTimeout(timer)
  }, [isActive, delayMs])

  return isVisible
}
