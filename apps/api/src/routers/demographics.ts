import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'

export const demographicsRouter = router({
  getData: publicProcedure.query(async () => {
    // Use SQL aggregation function to compute demographics in the database
    const { data, error } = await supabase.rpc('get_demographics_stats')

    if (error) {
      console.error('Error fetching demographics stats:', error)
      throw new Error('Failed to fetch demographics statistics')
    }

    if (!data || data.length === 0) {
      return {
        ageDistribution: [],
        sexDistribution: [],
        weightDistribution: []
      }
    }

    // Parse the result from the SQL function
    // The function returns rows with category, subcategory, and count
    const ageDistribution = data
      .filter((row: any) => row.category === 'age')
      .map((row: any) => ({
        range: row.subcategory,
        count: Number(row.count)
      }))

    const sexDistribution = data
      .filter((row: any) => row.category === 'sex')
      .map((row: any) => ({
        name: row.subcategory,
        value: Number(row.count)
      }))
      .filter((s: any) => s.value > 0)

    const weightDistribution = data
      .filter((row: any) => row.category === 'weight')
      .map((row: any) => ({
        range: row.subcategory,
        count: Number(row.count)
      }))

    return {
      ageDistribution,
      sexDistribution,
      weightDistribution
    }
  }),
})
