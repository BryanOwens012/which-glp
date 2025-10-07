import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'

export const locationsRouter = router({
  getData: publicProcedure.query(async () => {
    // Get all experiences with location data
    const { data: experiences } = await supabase
      .from('mv_experiences_denormalized')
      .select('location, cost_per_month, insurance_coverage')
      .not('location', 'is', null)

    if (!experiences || experiences.length === 0) {
      return []
    }

    // Group by location
    const locationMap = new Map<string, any[]>()
    experiences.forEach(exp => {
      const location = exp.location
      if (!locationMap.has(location)) {
        locationMap.set(location, [])
      }
      locationMap.get(location)!.push(exp)
    })

    const locationData = Array.from(locationMap.entries()).map(([location, exps]) => {
      // Calculate average cost
      const costData = exps.filter(e => e.cost_per_month)
      const avgCost = costData.length > 0
        ? costData.reduce((sum, e) => sum + e.cost_per_month, 0) / costData.length
        : null

      // Calculate insurance coverage rate
      const insuranceCount = exps.filter(e => e.insurance_coverage).length
      const insuranceRate = (insuranceCount / exps.length) * 100

      return {
        location,
        count: exps.length,
        avgCost,
        insuranceRate
      }
    })

    return locationData.sort((a, b) => b.count - a.count)
  }),
})
