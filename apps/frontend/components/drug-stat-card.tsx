import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { DrugStats } from "@/lib/types"
import { TrendingDown, Users, DollarSign, AlertCircle, ThumbsUp } from "lucide-react"

type DrugStatCardProps = {
  stats: DrugStats
  onClick?: () => void
}

/**
 * Comprehensive drug statistics card
 * Shows key metrics for a single drug
 */
export function DrugStatCard({ stats, onClick }: DrugStatCardProps) {
  const hasWeightLossData = stats.avgWeightLoss !== null
  const hasCostData = stats.avgCostPerMonth !== null

  return (
    <Card
      className="border-border/40 bg-card p-6 hover:border-primary/50 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold">{stats.drug === "GLP-1" ? "GLP-1 (General)" : stats.drug}</h3>
            <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              <span>{stats.count.toLocaleString()} experiences</span>
            </div>
          </div>
          {stats.avgRecommendationScore !== null && (
            <Badge
              variant={
                stats.avgRecommendationScore >= 0.7
                  ? "default"
                  : stats.avgRecommendationScore >= 0.4
                    ? "secondary"
                    : "outline"
              }
            >
              {Math.round(stats.avgRecommendationScore * 100)}% recommend
            </Badge>
          )}
        </div>

        {/* Weight Loss */}
        {hasWeightLossData && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <TrendingDown className="h-4 w-4 text-primary" />
                <span className="font-medium">Avg. Weight Loss</span>
              </div>
              <span className="text-2xl font-bold text-primary">
                {stats.avgWeightLoss?.toFixed(1) ?? 'N/A'}%
              </span>
            </div>
            {stats.avgWeightLossLbs && (
              <p className="text-xs text-muted-foreground">
                ~{Math.round(stats.avgWeightLossLbs)} lbs over{" "}
                {stats.avgDurationWeeks ? `${Math.round(stats.avgDurationWeeks / 4.33)} months` : "reported period"}
              </p>
            )}
          </div>
        )}

        {/* Sentiment Change */}
        {stats.avgSentimentPre !== null && stats.avgSentimentPost !== null && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Quality of Life Improvement</div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Before</span>
                  <span className="font-semibold">{Math.round(stats.avgSentimentPre * 100)}%</span>
                </div>
                <Progress value={stats.avgSentimentPre * 100} className="h-2" />
              </div>
              <span className="text-muted-foreground">→</span>
              <div className="flex-1">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-foreground">After</span>
                  <span className="font-semibold">{Math.round(stats.avgSentimentPost * 100)}%</span>
                </div>
                <Progress value={stats.avgSentimentPost * 100} className="h-2" />
              </div>
            </div>
          </div>
        )}

        {/* Cost */}
        {hasCostData && (
          <div className="flex items-center justify-between pt-2 border-t border-border/40">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Avg. Monthly Cost</span>
            </div>
            <span className="text-lg font-semibold">${Math.round(stats.avgCostPerMonth ?? 0)}</span>
          </div>
        )}

        {/* Insurance Coverage */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Insurance Coverage</span>
          <span className="text-sm font-semibold">{Math.round(stats.insuranceCoverage)}%</span>
        </div>

        {/* Common Side Effects */}
        {stats.commonSideEffects.length > 0 && (
          <div className="pt-2 border-t border-border/40">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <span className="text-sm font-medium">Most Common Side Effects</span>
            </div>
            <div className="space-y-1">
              {stats.commonSideEffects.slice(0, 3).map((effect) => (
                <div key={effect.name} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground capitalize">{effect.name}</span>
                  <span className="font-medium">{Math.round(effect.percentage)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Additional Stats */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border/40 text-xs">
          {stats.plateauRate > 0 && (
            <div>
              <div className="text-muted-foreground">Plateau Rate</div>
              <div className="font-semibold">{Math.round(stats.plateauRate)}%</div>
            </div>
          )}
          {stats.pharmacyAccessIssues > 0 && (
            <div>
              <div className="text-muted-foreground">Access Issues</div>
              <div className="font-semibold">{Math.round(stats.pharmacyAccessIssues)}%</div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
