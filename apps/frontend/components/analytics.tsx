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
    if (typeof window.gtag !== "undefined") {
      const url = pathname + (searchParams.toString() ? `?${searchParams.toString()}` : "")
      window.gtag("config", "G-1JJ2DG0KPD", {
        page_path: url,
      })
    }
  }, [pathname, searchParams])

  return null
}
