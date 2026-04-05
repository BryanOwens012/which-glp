import { router, publicProcedure } from '../lib/trpc.js'
import { captureEvent } from '../lib/posthog.js'
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

      captureEvent('api', 'recommendation_requested', {
        weight_loss_goal_pct: input.currentWeight > 0
          ? Math.round(((input.currentWeight - input.goalWeight) / input.currentWeight) * 100)
          : 0,
        age: input.age,
        sex: input.sex,
        state: input.state,
        has_insurance: input.hasInsurance,
        comorbidity_count: input.comorbidities.length,
        side_effect_concern_count: input.sideEffectConcerns.length,
      })

      try {
        // Get rec-engine API URL from environment or default to 127.0.0.1
        // On Railway: Use the REC_ENGINE_URL env var with the internal service URL
        // Locally: Use 127.0.0.1 instead of localhost to avoid IPv6 resolution issues
        let mlApiUrl = process.env.REC_ENGINE_URL?.trim() || 'http://127.0.0.1:8001'

        // Add protocol if not present
        // Use https:// for Railway domains (.railway.app), http:// for local
        if (!mlApiUrl.startsWith('http://') && !mlApiUrl.startsWith('https://')) {
          const protocol = mlApiUrl.includes('railway.app') ? 'https://' : 'http://'
          mlApiUrl = `${protocol}${mlApiUrl}`
        }

        console.log(`[REC ENGINE] Calling: ${mlApiUrl}/api/recommendations`)

        // Call FastAPI service
        const response = await fetch(`${mlApiUrl}/api/recommendations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-internal-api-key': process.env.INTERNAL_API_KEY ?? '',
          },
          body: JSON.stringify(input),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
          throw new Error(`Rec engine error: ${errorData.detail || response.statusText}`)
        }

        const result = await response.json()
        const processingTime = Date.now() - startTime

        captureEvent('api', 'recommendation_completed', {
          drug_count: result.recommendations.length,
          processing_time_ms: processingTime,
          top_drug: result.recommendations[0]?.drug,
          top_match_score: result.recommendations[0]?.matchScore,
        })

        return {
          recommendations: result.recommendations,
          processingTime,
        }
      } catch (error) {
        console.error('Recommendation error:', error)

        captureEvent('api', 'recommendation_failed', {
          error: error instanceof Error ? error.message : 'Unknown error',
          processing_time_ms: Date.now() - startTime,
        })

        // Return user-friendly error
        if (error instanceof Error) {
          throw new Error(`Failed to generate recommendations: ${error.message}`)
        }
        throw new Error('Failed to generate recommendations')
      }
    }),
})
