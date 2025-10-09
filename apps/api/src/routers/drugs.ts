import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'
import { withCache } from '../lib/redis.js'

export const drugsRouter = router({
  getAllStats: publicProcedure.query(async () => {
    // Cache key for all drug stats
    // This endpoint is called on initial /compare page load
    const cacheKey = 'drugs:all-stats'
    const cacheTTL = 3 * 24 * 60 * 60 // 3 days (259200 seconds)
    // Data refreshes every few days when new Reddit posts are ingested

    return withCache(cacheKey, cacheTTL, async () => {
      return await fetchAllDrugStats()
    })
  }),
})

/**
 * Fetch all drug statistics from database using SQL aggregations
 * This performs all calculations in the database rather than in TypeScript
 */
async function fetchAllDrugStats() {
  // Build SQL query to aggregate all stats per drug in a single query
  // This uses GROUP BY to compute statistics directly in PostgreSQL
  const { data, error } = await supabase.rpc('get_drug_stats')

  if (error) {
    console.error('Error fetching drug stats:', error)
    throw new Error('Failed to fetch drug statistics')
  }

  if (!data || data.length === 0) {
    return []
  }

  // For side effects and severity, we still need to do some post-processing
  // because we need to parse JSON arrays and aggregate across all experiences
  const drugStats = await Promise.all(data.map(async (drugData: any) => {
    // Fetch side effects for this drug to parse and aggregate
    const { data: sideEffectsData } = await supabase
      .from('mv_experiences_denormalized')
      .select('top_side_effects')
      .eq('primary_drug', drugData.drug)
      .not('top_side_effects', 'is', null)

    // Parse and aggregate side effects
    const allSideEffects = (sideEffectsData || []).flatMap(e => e.top_side_effects || [])
    const sideEffectCounts: Record<string, number> = {}
    const severityCounts = { mild: 0, moderate: 0, severe: 0 }

    allSideEffects.forEach(effect => {
      try {
        const parsed = typeof effect === 'string' ? JSON.parse(effect) : effect
        const effectName = parsed.name || effect

        // Count effect occurrences
        sideEffectCounts[effectName] = (sideEffectCounts[effectName] || 0) + 1

        // Count severity
        const severity = parsed.severity?.toLowerCase()
        if (severity === 'mild') severityCounts.mild++
        else if (severity === 'moderate') severityCounts.moderate++
        else if (severity === 'severe') severityCounts.severe++
      } catch {
        // If parsing fails, try to use the raw effect string
        const effectName = typeof effect === 'string' ? effect : String(effect)
        sideEffectCounts[effectName] = (sideEffectCounts[effectName] || 0) + 1
      }
    })

    // Calculate side effect reporting rate
    const usersWithSideEffects = sideEffectsData?.length || 0
    const sideEffectReportingRate = (usersWithSideEffects / drugData.count) * 100

    // Get top 10 common side effects
    const commonSideEffects = Object.entries(sideEffectCounts)
      .map(([name, count]) => ({
        name,
        count,
        percentage: (count / drugData.count) * 100
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)

    // Calculate side effect severity distribution
    const totalSeverity = severityCounts.mild + severityCounts.moderate + severityCounts.severe
    const sideEffectSeverity = totalSeverity > 0 ? {
      mild: (severityCounts.mild / totalSeverity) * 100,
      moderate: (severityCounts.moderate / totalSeverity) * 100,
      severe: (severityCounts.severe / totalSeverity) * 100
    } : {
      mild: 0,
      moderate: 0,
      severe: 0
    }

    return {
      drug: drugData.drug,
      count: drugData.count,
      avgWeightLoss: drugData.avg_weight_loss_percentage,
      avgWeightLossLbs: drugData.avg_weight_loss_lbs,
      avgDurationWeeks: drugData.avg_duration_weeks,
      avgCostPerMonth: drugData.avg_cost_per_month,
      avgSentimentPre: drugData.avg_sentiment_pre,
      avgSentimentPost: drugData.avg_sentiment_post,
      avgRecommendationScore: drugData.avg_recommendation_score,
      plateauRate: drugData.plateau_rate,
      reboundRate: drugData.rebound_rate,
      commonSideEffects,
      sideEffectSeverity,
      sideEffectReportingRate,
      insuranceCoverage: drugData.insurance_coverage_rate,
      drugSources: {
        brand: drugData.brand_count,
        compounded: drugData.compounded_count,
        outOfPocket: drugData.out_of_pocket_count,
        other: 0
      },
      pharmacyAccessIssues: 15 // Placeholder value
    }
  }))

  return drugStats.sort((a, b) => b.count - a.count)
}
