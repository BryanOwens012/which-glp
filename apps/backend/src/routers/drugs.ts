import { router, publicProcedure } from '../lib/trpc'
import { supabase } from '../lib/supabase'

export const drugsRouter = router({
  getAllStats: publicProcedure.query(async () => {
    // Get all experiences grouped by drug
    const { data: experiences } = await supabase
      .from('mv_experiences_denormalized')
      .select('*')
      .not('primary_drug', 'is', null)

    if (!experiences || experiences.length === 0) {
      return []
    }

    // Group by drug and calculate stats
    const drugMap = new Map<string, any[]>()
    experiences.forEach(exp => {
      const drug = exp.primary_drug
      if (!drugMap.has(drug)) {
        drugMap.set(drug, [])
      }
      drugMap.get(drug)!.push(exp)
    })

    const drugStats = Array.from(drugMap.entries()).map(([drug, exps]) => {
      // Weight loss stats
      const weightLossData = exps.filter(e => e.weight_loss_percentage !== null && e.weight_loss_percentage !== undefined)
      const avgWeightLoss = weightLossData.length > 0
        ? weightLossData.reduce((sum, e) => sum + e.weight_loss_percentage, 0) / weightLossData.length
        : null

      const weightLossLbsData = exps.filter(e => e.weight_loss_lbs !== null && e.weight_loss_lbs !== undefined)
      const avgWeightLossLbs = weightLossLbsData.length > 0
        ? weightLossLbsData.reduce((sum, e) => sum + e.weight_loss_lbs, 0) / weightLossLbsData.length
        : null

      // Duration stats
      const durationData = exps.filter(e => e.duration_weeks)
      const avgDurationWeeks = durationData.length > 0
        ? durationData.reduce((sum, e) => sum + e.duration_weeks, 0) / durationData.length
        : null

      // Cost stats
      const costData = exps.filter(e => e.cost_per_month)
      const avgCostPerMonth = costData.length > 0
        ? costData.reduce((sum, e) => sum + e.cost_per_month, 0) / costData.length
        : null

      // Sentiment stats
      const sentimentPreData = exps.filter(e => e.sentiment_pre !== null)
      const avgSentimentPre = sentimentPreData.length > 0
        ? sentimentPreData.reduce((sum, e) => sum + e.sentiment_pre, 0) / sentimentPreData.length
        : null

      const sentimentPostData = exps.filter(e => e.sentiment_post !== null)
      const avgSentimentPost = sentimentPostData.length > 0
        ? sentimentPostData.reduce((sum, e) => sum + e.sentiment_post, 0) / sentimentPostData.length
        : null

      // Recommendation stats
      const recommendationData = exps.filter(e => e.recommendation_score !== null)
      const avgRecommendationScore = recommendationData.length > 0
        ? recommendationData.reduce((sum, e) => sum + e.recommendation_score, 0) / recommendationData.length
        : null

      // Plateau and rebound rates
      const plateauCount = exps.filter(e => e.plateau).length
      const reboundCount = exps.filter(e => e.rebound).length
      const plateauRate = (plateauCount / exps.length) * 100
      const reboundRate = (reboundCount / exps.length) * 100

      // Side effects
      const allSideEffects = exps.flatMap(e => e.top_side_effects || [])
      const sideEffectCounts = allSideEffects.reduce((acc, effect) => {
        acc[effect] = (acc[effect] || 0) + 1
        return acc
      }, {} as Record<string, number>)

      const commonSideEffects = Object.entries(sideEffectCounts)
        .map(([name, count]): { name: string; count: number; percentage: number } => ({
          name,
          count: count as number,
          percentage: ((count as number) / exps.length) * 100
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)

      // Side effect severity - calculate from actual data
      const severityCounts = { mild: 0, moderate: 0, severe: 0 }
      allSideEffects.forEach(effect => {
        try {
          const parsed = typeof effect === 'string' ? JSON.parse(effect) : effect
          const severity = parsed.severity?.toLowerCase()
          if (severity === 'mild') severityCounts.mild++
          else if (severity === 'moderate') severityCounts.moderate++
          else if (severity === 'severe') severityCounts.severe++
        } catch {
          // If parsing fails, skip this effect
        }
      })

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

      // Insurance coverage
      const insuranceCount = exps.filter(e => e.insurance_coverage).length
      const insuranceCoverage = (insuranceCount / exps.length) * 100

      // Drug sources (placeholder - need to add to extraction)
      const drugSources = {
        brand: exps.filter(e => e.drug_source === 'brand').length,
        compounded: exps.filter(e => e.drug_source === 'compounded').length,
        outOfPocket: exps.filter(e => e.out_of_pocket_cost).length,
        other: 0
      }

      // Pharmacy access issues (placeholder)
      const pharmacyAccessIssues = 15

      return {
        drug,
        count: exps.length,
        avgWeightLoss,
        avgWeightLossLbs,
        avgDurationWeeks,
        avgCostPerMonth,
        avgSentimentPre,
        avgSentimentPost,
        avgRecommendationScore,
        plateauRate,
        reboundRate,
        commonSideEffects,
        sideEffectSeverity,
        insuranceCoverage,
        drugSources,
        pharmacyAccessIssues
      }
    })

    return drugStats.sort((a, b) => b.count - a.count)
  }),
})
