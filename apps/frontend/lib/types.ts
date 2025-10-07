/**
 * TypeScript types for WhichGLP frontend
 * Mirrors the database schema from extracted_features table
 */

export type WeightData = {
  value: number | null
  unit: "lbs" | "kg" | null
  confidence: "high" | "medium" | "low" | null
}

export type SideEffect = {
  name: string
  severity: "mild" | "moderate" | "severe" | null
  confidence: "high" | "medium" | "low" | null
}

export type Sex = "male" | "female" | "ftm" | "mtf" | "other"

export type DrugSource = "brand" | "compounded" | "out-of-pocket" | "other"

export type Currency = "USD" | "CAD" | "GBP" | "EUR" | "AUD"

/**
 * Complete extracted features from a Reddit post or comment
 */
export type ExtractedFeature = {
  // IDs
  id: string
  post_id: string | null
  comment_id: string | null

  // Core data
  summary: string
  beginning_weight: WeightData | null
  end_weight: WeightData | null
  duration_weeks: number | null
  cost_per_month: number | null
  currency: Currency

  // Drugs
  drugs_mentioned: string[]
  primary_drug: string | null
  drug_sentiments: Record<string, number>

  // Sentiment
  sentiment_pre: number | null
  sentiment_post: number | null
  recommendation_score: number | null

  // Insurance
  has_insurance: boolean | null
  insurance_provider: string | null

  // Health
  side_effects: SideEffect[]
  comorbidities: string[]
  location: string | null

  // Demographics
  age: number | null
  sex: Sex | null
  state: string | null
  country: string | null

  // Metadata
  model_used: string
  confidence_score: number | null
  processing_cost_usd: number | null
  tokens_input: number | null
  tokens_output: number | null
  processing_time_ms: number | null
  processed_at: string

  // Extended features
  dosage_progression: string | null
  exercise_frequency: string | null
  dietary_changes: string | null
  previous_weight_loss_attempts: string[]
  drug_source: DrugSource | null
  switching_drugs: string | null
  side_effect_timing: string | null
  side_effect_resolution: number | null
  food_intolerances: string[]
  plateau_mentioned: boolean | null
  rebound_weight_gain: boolean | null
  labs_improvement: string[]
  medication_reduction: string[]
  nsv_mentioned: string[]
  support_system: string | null
  pharmacy_access_issues: boolean | null
  mental_health_impact: string | null

  raw_response: any
}

/**
 * Aggregated statistics for a specific drug
 */
export type DrugStats = {
  drug: string
  count: number
  avgWeightLoss: number | null
  avgWeightLossLbs: number | null
  avgDurationWeeks: number | null
  avgCostPerMonth: number | null
  avgSentimentPre: number | null
  avgSentimentPost: number | null
  avgRecommendationScore: number | null
  insuranceCoverage: number // percentage
  commonSideEffects: Array<{
    name: string
    count: number
    percentage: number
  }>
  sideEffectSeverity: {
    mild: number
    moderate: number
    severe: number
  }
  drugSources: {
    brand: number
    compounded: number
    outOfPocket: number
    other: number
  }
  pharmacyAccessIssues: number // percentage
  plateauRate: number // percentage
  reboundRate: number // percentage
}

/**
 * Geographic cost and availability data
 */
export type LocationData = {
  location: string // city, state, or country
  count: number
  avgCost: number | null
  pharmacyAccessIssues: number // percentage
  topDrugs: Array<{
    drug: string
    count: number
  }>
}

/**
 * Demographic breakdown
 */
export type DemographicData = {
  ageRanges: Array<{
    range: string
    count: number
  }>
  sexDistribution: Array<{
    sex: Sex | "unknown"
    count: number
  }>
  topComorbidities: Array<{
    condition: string
    count: number
  }>
}

/**
 * User experience card (for /experiences page)
 */
export type ExperienceCard = {
  id: string
  post_id: string | null
  comment_id: string | null
  summary: string
  primary_drug: string | null
  weightLoss: number | null // calculated from beginning_weight -> end_weight
  weightLossUnit: "lbs" | "kg" | null
  beginning_weight: WeightData | null
  end_weight: WeightData | null
  duration_weeks: number | null
  sentiment_post: number | null
  recommendation_score: number | null
  top_side_effects: string[] // top 3
  cost_per_month: number | null
  age: number | null
  sex: Sex | null
  location: string | null
  processed_at: string
  created_at: string | null // Reddit post/comment creation date
}

/**
 * Prediction input from user
 */
export type PredictionInput = {
  currentWeight: number
  weightUnit: "lbs" | "kg"
  goalWeight: number
  age: number
  sex: Sex
  state?: string
  country: string
  comorbidities: string[]
  hasInsurance: boolean
  insuranceProvider?: string
  maxBudget: number | null
  sideEffectConcerns: string[]
}

/**
 * Prediction result for a drug
 */
export type PredictionResult = {
  drug: string
  matchScore: number // 0-100, how well this drug matches the user's profile
  expectedWeightLoss: {
    min: number
    max: number
    avg: number
    unit: "lbs" | "kg"
  }
  successRate: number // percentage of similar users who achieved goals
  estimatedCost: number | null
  sideEffectProbability: Array<{
    effect: string
    probability: number // percentage
    severity: "mild" | "moderate" | "severe"
  }>
  similarUserCount: number
  pros: string[]
  cons: string[]
}

/**
 * Reddit post/comment reference
 */
export type RedditReference = {
  type: "post" | "comment"
  id: string // post_id or comment_id without prefix
  subreddit?: string // if available
}

/**
 * Utility function to get Reddit permalink
 */
export function getRedditPermalink(ref: RedditReference): string {
  // Reddit IDs are stored with prefixes (t3_ for posts, t1_ for comments)
  // Remove prefix if present
  const cleanId = ref.id.replace(/^t[13]_/, "")

  if (ref.type === "post") {
    // Post permalink format: https://reddit.com/comments/{post_id}
    return `https://reddit.com/comments/${cleanId}`
  } else {
    // Comment permalink format: https://reddit.com/comments/_/{comment_id}
    return `https://reddit.com/comments/_/_/${cleanId}`
  }
}

/**
 * Parse Reddit reference from extracted feature
 */
export function getRedditReference(feature: Pick<ExtractedFeature, "post_id" | "comment_id">): RedditReference | null {
  if (feature.comment_id) {
    return {
      type: "comment",
      id: feature.comment_id,
    }
  } else if (feature.post_id) {
    return {
      type: "post",
      id: feature.post_id,
    }
  }
  return null
}

/**
 * Calculate weight loss from beginning to end weight
 */
export function calculateWeightLoss(
  beginning: WeightData | null,
  end: WeightData | null
): { amount: number; unit: "lbs" | "kg" } | null {
  if (!beginning?.value || !end?.value || !beginning.unit || !end.unit) {
    return null
  }

  // Convert to same unit if needed
  let beginningLbs = beginning.value
  let endLbs = end.value

  if (beginning.unit === "kg") {
    beginningLbs = beginning.value * 2.20462
  }
  if (end.unit === "kg") {
    endLbs = end.value * 2.20462
  }

  const lossLbs = beginningLbs - endLbs

  // Return in original unit
  if (beginning.unit === "kg") {
    return { amount: lossLbs / 2.20462, unit: "kg" }
  }
  return { amount: lossLbs, unit: "lbs" }
}

/**
 * Calculate weight loss percentage
 */
export function calculateWeightLossPercentage(
  beginning: WeightData | null,
  end: WeightData | null
): number | null {
  if (!beginning?.value || !end?.value || !beginning.unit || !end.unit) {
    return null
  }

  // Convert to same unit
  let beginningValue = beginning.value
  let endValue = end.value

  if (beginning.unit === "kg" && end.unit === "lbs") {
    endValue = end.value / 2.20462
  } else if (beginning.unit === "lbs" && end.unit === "kg") {
    endValue = end.value * 2.20462
  }

  const percentageLoss = ((beginningValue - endValue) / beginningValue) * 100
  return Math.round(percentageLoss * 10) / 10 // Round to 1 decimal
}

/**
 * Format weight for display
 */
export function formatWeight(weight: WeightData | null): string {
  if (!weight?.value || !weight.unit) {
    return "N/A"
  }
  return `${Math.round(weight.value)} ${weight.unit}`
}

/**
 * Format duration for display
 */
export function formatDuration(weeks: number | null): string {
  if (!weeks) return "N/A"

  if (weeks < 4) {
    return `${weeks} week${weeks !== 1 ? "s" : ""}`
  }

  const months = Math.round(weeks / 4.33)
  return `${months} month${months !== 1 ? "s" : ""}`
}

/**
 * Format cost for display
 */
export function formatCost(cost: number | null, currency: Currency = "USD"): string {
  if (!cost) return "N/A"

  const currencySymbols: Record<Currency, string> = {
    USD: "$",
    CAD: "CA$",
    GBP: "£",
    EUR: "€",
    AUD: "A$",
  }

  return `${currencySymbols[currency]}${Math.round(cost)}`
}

/**
 * Format sentiment score (0-1) to percentage
 */
export function formatSentiment(score: number | null): string {
  if (score === null) return "N/A"
  return `${Math.round(score * 100)}%`
}

/**
 * Get sentiment color class
 */
export function getSentimentColor(score: number | null): string {
  if (score === null) return "text-muted-foreground"
  if (score >= 0.7) return "text-primary"
  if (score >= 0.4) return "text-yellow-600"
  return "text-destructive"
}
