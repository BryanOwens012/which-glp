import { router, publicProcedure } from '../lib/trpc.js'
import { supabase } from '../lib/supabase.js'
import { z } from 'zod'

// Strongly typed enums for sorting
const SortField = z.enum([
  'date',
  'rating',
  'duration',
  'startWeight',
  'endWeight',
  'weightChange',
  'weightLossPercent',
  'weightLossSpeed',
  'weightLossSpeedPercent'
])
const SortDirection = z.enum(['asc', 'desc'])

type SortFieldType = z.infer<typeof SortField>
type SortDirectionType = z.infer<typeof SortDirection>

export const experiencesRouter = router({
  list: publicProcedure
    .input(z.object({
      // Filters
      drug: z.string().optional(),
      search: z.string().optional(),

      // Pagination (using cursor for tRPC infinite queries)
      limit: z.number().min(1).max(100).default(20),
      cursor: z.number().min(0).optional(),

      // Sorting
      sortBy: SortField.optional(),
      sortOrder: SortDirection.optional(),
    }))
    .query(async ({ input }) => {
      const offset = input.cursor ?? 0
      const sortBy: SortFieldType = input.sortBy ?? 'date'
      const sortOrder: SortDirectionType = input.sortOrder ?? 'desc'

      // Map frontend sort fields to database columns
      const columnMap: Record<SortFieldType, string> = {
        date: 'created_at',
        rating: 'sentiment_post',
        duration: 'duration_weeks',
        startWeight: 'beginning_weight',
        endWeight: 'end_weight',
        weightChange: 'weight_loss_lbs',
        weightLossPercent: 'weight_loss_percentage',
        weightLossSpeed: 'weight_loss_speed_lbs_per_month',
        weightLossSpeedPercent: 'weight_loss_speed_percent_per_month',
      }

      const sortColumn = columnMap[sortBy]
      const ascending = sortOrder === 'asc'

      // Step 1: Build base query with filters, ordering, and pagination ALL in the database query
      let dataQuery = supabase
        .from('mv_experiences_denormalized')
        .select('*', { count: 'exact' })

      // Apply filters
      if (input.drug) {
        dataQuery = dataQuery.eq('primary_drug', input.drug)
      }

      if (input.search) {
        dataQuery = dataQuery.ilike('summary', `%${input.search}%`)
      }

      // Apply ordering in the database
      dataQuery = dataQuery.order(sortColumn, { ascending, nullsFirst: false })

      // Apply pagination in the database
      dataQuery = dataQuery.range(offset, offset + input.limit - 1)

      // Execute the query
      const { data, error, count } = await dataQuery

      if (error) {
        console.error('Supabase error:', error)
        throw new Error('Failed to fetch experiences')
      }

      // Map feature_id to id for frontend compatibility
      const mappedData = (data || []).map((experience: any) => ({
        ...experience,
        id: experience.feature_id,
      }))

      return {
        experiences: mappedData,
        total: count || 0,
      }
    }),

  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      const { data, error} = await supabase
        .from('mv_experiences_denormalized')
        .select('*')
        .eq('feature_id', input.id)
        .single()

      if (error) {
        console.error('Supabase error:', error)
        throw new Error('Experience not found')
      }

      // Map feature_id to id for frontend compatibility
      return {
        ...data,
        id: data.feature_id,
      }
    }),
})
