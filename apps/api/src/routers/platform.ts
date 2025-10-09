import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'
import { z } from 'zod'

export const platformRouter = router({
  getStats: publicProcedure.query(async () => {
    // Use SQL aggregation function to compute platform stats in the database
    const { data, error } = await supabase.rpc('get_platform_stats')

    if (error) {
      console.error('Error fetching platform stats:', error)
      throw new Error('Failed to fetch platform statistics')
    }

    // The function returns a single row, so take the first element
    const stats = data?.[0]

    if (!stats) {
      return {
        totalExperiences: 0,
        uniqueDrugs: 0,
        locationsTracked: 0,
        avgWeightLossPercentage: 0,
      }
    }

    return {
      totalExperiences: Number(stats.total_experiences) || 0,
      uniqueDrugs: Number(stats.unique_drugs) || 0,
      locationsTracked: Number(stats.locations_tracked) || 0,
      avgWeightLossPercentage: 0, // Placeholder - not calculated in SQL function yet
    }
  }),

  getTrends: publicProcedure
    .input(z.object({ period: z.enum(['week', 'month', 'year']) }))
    .query(async ({ input }) => {
      // For now, return empty trends - will implement when we have timestamp data
      return []
    }),
})
