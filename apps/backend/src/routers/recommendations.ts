import { router, publicProcedure } from '../lib/trpc.js'
import { z } from 'zod'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'
import { fileURLToPath } from 'url'

const execAsync = promisify(exec)

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

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
        // Path to the Python ML script
        const repoRoot = path.resolve(__dirname, '../../../..')
        const pythonScript = path.join(repoRoot, 'apps/backend/ml/recommender_api.py')
        const venvPython = path.join(repoRoot, 'venv/bin/python3')

        // Serialize input to JSON for Python
        const inputJson = JSON.stringify(input)

        // Execute Python script
        const { stdout, stderr } = await execAsync(
          `${venvPython} ${pythonScript} '${inputJson}'`,
          {
            cwd: path.join(repoRoot, 'apps/backend'),
            timeout: 30000, // 30 second timeout
            maxBuffer: 1024 * 1024 * 10, // 10MB buffer
          }
        )

        if (stderr && !stderr.includes('INFO')) {
          console.error('Python stderr:', stderr)
        }

        // Parse Python output
        const result = JSON.parse(stdout)

        if (result.error) {
          throw new Error(result.error)
        }

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
