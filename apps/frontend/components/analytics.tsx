"use client"

import { useEffect } from "react"
import { usePathname, useSearchParams } from "next/navigation"

declare global {
  interface Window {
    gtag?: (
      command: string,
      targetId: string,
      config?: { page_path: string }
    ) => void
  }
}

export function Analytics() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    const GA_TAG = process.env.NEXT_PUBLIC_GA_TAG
    if (GA_TAG && typeof window.gtag !== "undefined") {
      const url = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : "")
      window.gtag("config", GA_TAG, {
        page_path: url,
      })
    }
  }, [pathname, searchParams])

  return null
}
