import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'

export const locationsRouter = router({
  getData: publicProcedure.query(async () => {
    // Use SQL aggregation function to compute location stats in the database
    const { data, error } = await supabase.rpc('get_location_stats')

    if (error) {
      console.error('Error fetching location stats:', error)
      throw new Error('Failed to fetch location statistics')
    }

    if (!data || data.length === 0) {
      return []
    }

    // Map the database result to the expected frontend format
    return data.map((row: any) => ({
      location: row.location,
      count: Number(row.count),
      avgCost: row.avg_cost ? Number(row.avg_cost) : null,
      insuranceRate: Number(row.insurance_rate)
    }))
  }),
})
