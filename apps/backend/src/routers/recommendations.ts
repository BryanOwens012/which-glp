import { router, publicProcedure } from '../lib/trpc.js'
import { z } from 'zod'

// Input validation schema
const RecommendationInput = z.object({
  currentWeight: z.number().positive(),
  weightUnit: z.enum(['lbs', 'kg']),
  goalWeight: z.number().positive(),
  age: z.number().int().min(18).max(100).optional(),
  sex: z.enum(['male', 'female', 'other']).optional(),
  state: z.string().optional(),
  country: z.string().default('USA'),
  comorbidities: z.array(z.string()).default([]),
  hasInsurance: z.boolean().default(false),
  insuranceProvider: z.string().optional(),
  maxBudget: z.number().positive().optional(),
  sideEffectConcerns: z.array(z.string()).default([]),
})

// Output types
const SideEffectProbability = z.object({
  effect: z.string(),
  probability: z.number(),
  severity: z.enum(['mild', 'moderate', 'severe']),
})

const ExpectedWeightLoss = z.object({
  min: z.number(),
  max: z.number(),
  avg: z.number(),
  unit: z.string(),
})

const Recommendation = z.object({
  drug: z.string(),
  matchScore: z.number(),
  expectedWeightLoss: ExpectedWeightLoss,
  successRate: z.number(),
  estimatedCost: z.number().nullable(),
  sideEffectProbability: z.array(SideEffectProbability),
  similarUserCount: z.number(),
  pros: z.array(z.string()),
  cons: z.array(z.string()),
})

export const recommendationsRouter = router({
  getForUser: publicProcedure
    .input(RecommendationInput)
    .output(z.object({
      recommendations: z.array(Recommendation),
      processingTime: z.number(),
    }))
    .mutation(async ({ input }) => {
      const startTime = Date.now()

      try {
        // Get ML API URL from environment or default to 127.0.0.1
        // On Railway: Use the ML_URL env var with the internal service URL
        // Locally: Use 127.0.0.1 instead of localhost to avoid IPv6 resolution issues
        let mlApiUrl = process.env.ML_URL?.trim() || 'http://127.0.0.1:8001'

        // Add protocol if not present
        // Use https:// for Railway domains (.railway.app), http:// for local
        if (!mlApiUrl.startsWith('http://') && !mlApiUrl.startsWith('https://')) {
          const protocol = mlApiUrl.includes('railway.app') ? 'https://' : 'http://'
          mlApiUrl = `${protocol}${mlApiUrl}`
        }

        console.log(`[ML API] Calling: ${mlApiUrl}/api/recommendations`)

        // Call FastAPI service
        const response = await fetch(`${mlApiUrl}/api/recommendations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(input),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
          throw new Error(`ML API error: ${errorData.detail || response.statusText}`)
        }

        const result = await response.json()
        const processingTime = Date.now() - startTime

        return {
          recommendations: result.recommendations,
          processingTime,
        }
      } catch (error) {
        console.error('Recommendation error:', error)

        // Return user-friendly error
        if (error instanceof Error) {
          throw new Error(`Failed to generate recommendations: ${error.message}`)
        }
        throw new Error('Failed to generate recommendations')
      }
    }),
})
