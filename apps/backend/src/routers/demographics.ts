import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'

export const demographicsRouter = router({
  getData: publicProcedure.query(async () => {
    // Get all experiences with demographic data
    const { data: experiences } = await supabase
      .from('mv_experiences_denormalized')
      .select('age, sex, starting_weight')

    if (!experiences || experiences.length === 0) {
      return {
        ageDistribution: [],
        sexDistribution: [],
        weightDistribution: []
      }
    }

    // Age distribution
    const ageRanges = {
      '18-24': 0,
      '25-34': 0,
      '35-44': 0,
      '45-54': 0,
      '55-64': 0,
      '65+': 0
    }

    experiences.forEach(exp => {
      const age = exp.age
      if (!age) return

      if (age >= 18 && age <= 24) ageRanges['18-24']++
      else if (age >= 25 && age <= 34) ageRanges['25-34']++
      else if (age >= 35 && age <= 44) ageRanges['35-44']++
      else if (age >= 45 && age <= 54) ageRanges['45-54']++
      else if (age >= 55 && age <= 64) ageRanges['55-64']++
      else if (age >= 65) ageRanges['65+']++
    })

    const ageDistribution = Object.entries(ageRanges).map(([range, count]) => ({
      range,
      count
    }))

    // Sex distribution
    const sexCounts = { male: 0, female: 0, other: 0 }
    experiences.forEach(exp => {
      const sex = exp.sex?.toLowerCase()
      if (sex === 'male' || sex === 'm') sexCounts.male++
      else if (sex === 'female' || sex === 'f') sexCounts.female++
      else if (sex) sexCounts.other++
    })

    const sexDistribution = [
      { name: 'Male', value: sexCounts.male },
      { name: 'Female', value: sexCounts.female },
      { name: 'Other', value: sexCounts.other }
    ].filter(s => s.value > 0)

    // Weight distribution
    const weightRanges = {
      '100-150': 0,
      '150-200': 0,
      '200-250': 0,
      '250-300': 0,
      '300+': 0
    }

    experiences.forEach(exp => {
      const weight = exp.starting_weight
      if (!weight) return

      if (weight >= 100 && weight < 150) weightRanges['100-150']++
      else if (weight >= 150 && weight < 200) weightRanges['150-200']++
      else if (weight >= 200 && weight < 250) weightRanges['200-250']++
      else if (weight >= 250 && weight < 300) weightRanges['250-300']++
      else if (weight >= 300) weightRanges['300+']++
    })

    const weightDistribution = Object.entries(weightRanges).map(([range, count]) => ({
      range,
      count
    }))

    return {
      ageDistribution,
      sexDistribution,
      weightDistribution
    }
  }),
})
