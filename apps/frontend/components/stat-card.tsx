import { Card } from "@/components/ui/card"
import { LucideIcon } from "lucide-react"

type StatCardProps = {
  title: string
  value: string | number
  subtitle?: string
  icon?: LucideIcon
  trend?: {
    value: string
    direction: "up" | "down" | "neutral"
  }
  valueClassName?: string
}

/**
 * Reusable stat card for dashboards
 */
export function StatCard({ title, value, subtitle, icon: Icon, trend, valueClassName }: StatCardProps) {
  return (
    <Card className="border-border/40 bg-card p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className={`mt-1 text-3xl font-bold ${valueClassName || ""}`}>{value}</p>
          {subtitle && <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>}
          {trend && (
            <div
              className={`mt-2 flex items-center gap-1 text-sm ${
                trend.direction === "up"
                  ? "text-primary"
                  : trend.direction === "down"
                    ? "text-destructive"
                    : "text-muted-foreground"
              }`}
            >
              <span>{trend.value}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 shrink-0">
            <Icon className="h-6 w-6 text-primary" />
          </div>
        )}
      </div>
    </Card>
  )
}
