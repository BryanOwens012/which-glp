import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { RedditLink } from "@/components/reddit-link"
import {
  ExperienceCard as ExperienceCardType,
  getRedditReference,
  formatDuration,
  formatCost,
  getRatingColor,
  getSideEffectColor,
  sortSideEffects,
} from "@/lib/types"
import { TrendingDown, Clock, AlertCircle, Star } from "lucide-react"

type ExperienceCardProps = {
  experience: ExperienceCardType
  onClick?: () => void
}

/**
 * Card displaying a single user experience
 * Used on /experiences page and in search results
 */
export function ExperienceCard({ experience, onClick }: ExperienceCardProps) {
  const redditRef = getRedditReference(experience)

  // Calculate weight loss display with percentage
  const beginWeight = experience.beginning_weight?.value
  const endWeight = experience.end_weight?.value
  const weightUnit = experience.beginning_weight?.unit || experience.end_weight?.unit

  const weightLoss = beginWeight && endWeight ? beginWeight - endWeight : experience.weightLoss
  const weightLossPercent = beginWeight && endWeight ? ((beginWeight - endWeight) / beginWeight) * 100 : null

  const weightLossDisplay = weightLoss && (weightUnit || experience.weightLossUnit)
    ? `${Math.round(weightLoss)} ${weightUnit || experience.weightLossUnit}${weightLossPercent ? ` (${weightLossPercent.toFixed(1)}%)` : ''}`
    : null

  // Calculate loss speed (per month)
  const durationMonths = experience.duration_weeks ? experience.duration_weeks / 4.33 : null
  const lossPerMonth = weightLoss && durationMonths && durationMonths > 0 ? weightLoss / durationMonths : null
  const lossPercentPerMonth = weightLossPercent && durationMonths && durationMonths > 0 ? weightLossPercent / durationMonths : null

  const lossSpeedDisplay = lossPerMonth && (weightUnit || experience.weightLossUnit)
    ? `${lossPerMonth.toFixed(1)} ${weightUnit || experience.weightLossUnit}/mo${lossPercentPerMonth ? ` (${lossPercentPerMonth.toFixed(1)}%/mo)` : ''}`
    : null

  // Format post date
  const postDate = experience.created_at
    ? new Date(experience.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : null

  return (
    <Card
      className="border-border/40 bg-card p-6 hover:border-primary/50 transition-colors cursor-pointer relative"
      onClick={onClick}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            {experience.primary_drug && (
              <Badge variant="default" className="mb-2">
                {experience.primary_drug}
              </Badge>
            )}
            <p className="text-sm text-muted-foreground line-clamp-3">
              {experience.summary}
            </p>
          </div>
          <div className="shrink-0 mt-1 relative z-10">
            {redditRef && <RedditLink reference={redditRef} />}
          </div>
        </div>

        {/* Stats Grid - Always show all 4 fields when available */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/40">
          {/* Rating */}
          {experience.sentiment_post !== null && (
            <div className="flex items-center gap-2">
              <Star className={`h-4 w-4 ${getRatingColor(experience.sentiment_post)}`} />
              <div>
                <div
                  className={`text-sm font-semibold ${getRatingColor(experience.sentiment_post)}`}
                >
                  {(experience.sentiment_post * 10).toFixed(1)}
                </div>
                <div className="text-xs text-muted-foreground">Rating</div>
              </div>
            </div>
          )}

          {/* Duration */}
          {experience.duration_weeks && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="text-sm font-semibold">{formatDuration(experience.duration_weeks)}</div>
                <div className="text-xs text-muted-foreground">Duration</div>
              </div>
            </div>
          )}

          {/* Weight Loss */}
          {weightLossDisplay && (
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-primary" />
              <div>
                <div className="text-sm font-semibold">{weightLossDisplay}</div>
                <div className="text-xs text-muted-foreground">Loss</div>
              </div>
            </div>
          )}

          {/* Loss Speed */}
          {lossSpeedDisplay && (
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-foreground" />
              <div>
                <div className="text-sm font-semibold">{lossSpeedDisplay}</div>
                <div className="text-xs text-muted-foreground">Loss Speed</div>
              </div>
            </div>
          )}
        </div>

        {/* Side Effects */}
        {experience.side_effects && experience.side_effects.length > 0 && (
          <div className="flex items-start gap-2 pt-4 border-t border-border/40">
            <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-medium text-muted-foreground mb-1">Side Effects</div>
              <div className="flex flex-wrap gap-1">
                {sortSideEffects(experience.side_effects).slice(0, 5).map((effect, index) => (
                  <Badge
                    key={`${effect.name}-${index}`}
                    variant="outline"
                    className={`text-xs text-white border-0 ${getSideEffectColor(effect.severity)}`}
                  >
                    {effect.name.charAt(0).toUpperCase() + effect.name.slice(1)}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Demographics */}
        {(experience.age || experience.sex || experience.location) && (
          <div className="text-xs text-muted-foreground pt-2 border-t border-border/40">
            {experience.age && <span>{experience.age}yo</span>}
            {experience.age && experience.sex && <span> • </span>}
            {experience.sex && <span className="capitalize">{experience.sex}</span>}
            {(experience.age || experience.sex) && experience.location && <span> • </span>}
            {experience.location && <span>{experience.location}</span>}
          </div>
        )}

        {/* Post Date */}
        {postDate && (
          <div className="text-xs text-muted-foreground pt-2">
            {(experience.age || experience.sex || experience.location) && <span> • </span>}
            Posted {postDate}
          </div>
        )}
      </div>
    </Card>
  )
}
