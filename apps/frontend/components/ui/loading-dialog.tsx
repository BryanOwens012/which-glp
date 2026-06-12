"use client"

import { Spinner } from '@/components/ui/spinner'
import { useDelayedVisible, LOADING_INDICATOR_DELAY_MS } from '@/hooks/use-delayed-visible'
import { cn } from '@/lib/utils'

type LoadingDialogProps = {
  isOpen: boolean
  message?: string
  /** How long the load must run before the dialog appears (avoids flashes). */
  delayMs?: number
  className?: string
}

/**
 * Small floating loading dialog for button-triggered loads that exceed
 * `delayMs` (default 200ms). Deliberately rendered WITHOUT a scrim/backdrop:
 * a scrim flashing in and out on short loads is worse UI than no indicator,
 * and the page behind stays interactive.
 */
export const LoadingDialog = ({
  isOpen,
  message = 'Loading…',
  delayMs = LOADING_INDICATOR_DELAY_MS,
  className,
}: LoadingDialogProps) => {
  const isVisible = useDelayedVisible(isOpen, delayMs)

  if (!isVisible) return null

  return (
    <div
      data-slot="loading-dialog"
      role="status"
      aria-live="polite"
      className={cn(
        'fixed left-1/2 top-1/2 z-50 flex -translate-x-1/2 -translate-y-1/2 items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 shadow-lg',
        className
      )}
    >
      <Spinner aria-hidden="true" className="text-primary" />
      <span className="text-sm text-card-foreground">{message}</span>
    </div>
  )
}
