import { router, publicProcedure } from '../lib/trpc'
import { supabase } from '../lib/supabase'
import { z } from 'zod'

export const platformRouter = router({
  getStats: publicProcedure.query(async () => {
    // Get total experiences
    const { count: totalExperiences } = await supabase
      .from('mv_experiences_denormalized')
      .select('*', { count: 'exact', head: true })

    // Get unique drugs
    const { data: drugs } = await supabase
      .from('mv_experiences_denormalized')
      .select('primary_drug')
      .not('primary_drug', 'is', null)

    const uniqueDrugs = new Set(drugs?.map(d => d.primary_drug) || []).size

    // Get unique locations
    const { data: locations } = await supabase
      .from('mv_experiences_denormalized')
      .select('location')
      .not('location', 'is', null)

    const locationsTracked = new Set(locations?.map(l => l.location) || []).size

    // Get average weight loss percentage
    const { data: weightLossData } = await supabase
      .from('mv_experiences_denormalized')
      .select('weightLoss, weightLossUnit')
      .not('weightLoss', 'is', null)
      .not('weightLossUnit', 'is', null)

    const avgWeightLossPercentage = weightLossData && weightLossData.length > 0
      ? weightLossData
          .filter(w => w.weightLossUnit === 'percent')
          .reduce((sum, w) => sum + (w.weightLoss || 0), 0) / 
          weightLossData.filter(w => w.weightLossUnit === 'percent').length || 0
      : 0

    return {
      totalExperiences: totalExperiences || 0,
      uniqueDrugs,
      locationsTracked,
      avgWeightLossPercentage,
    }
  }),

  getTrends: publicProcedure
    .input(z.object({ period: z.enum(['week', 'month', 'year']) }))
    .query(async ({ input }) => {
      // For now, return empty trends - will implement when we have timestamp data
      return []
    }),
})
