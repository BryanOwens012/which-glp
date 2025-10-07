import { router, publicProcedure } from '../lib/trpc'
import { supabase } from '../lib/supabase'
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

      // Pagination
      limit: z.number().min(1).max(100).default(20),
      offset: z.number().min(0).optional(),

      // Sorting
      sortBy: SortField.optional(),
      sortOrder: SortDirection.optional(),
    }))
    .query(async ({ input }) => {
      const offset = input.offset ?? 0
      const sortBy: SortFieldType = input.sortBy ?? 'date'
      const sortOrder: SortDirectionType = input.sortOrder ?? 'desc'

      let query = supabase
        .from('mv_experiences_denormalized')
        .select('*', { count: 'exact' })

      // Only show posts (not comments) AND ensure we only get ONE row per post_id
      // by selecting only rows where the feature was extracted from the post itself
      query = query.is('comment_id', null)

      if (input.drug) {
        query = query.eq('primary_drug', input.drug)
      }

      if (input.search) {
        query = query.ilike('summary', `%${input.search}%`)
      }

      // Apply sorting BEFORE pagination - this is critical for consistent results
      switch (sortBy) {
        case 'date':
          query = query
            .order('created_at', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'rating':
          query = query
            .order('recommendation_score', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'duration':
          query = query
            .order('duration_weeks', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'startWeight':
          query = query
            .order('beginning_weight->value', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'endWeight':
          query = query
            .order('end_weight->value', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'weightChange':
          query = query
            .order('weight_loss_lbs', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'weightLossPercent':
          query = query
            .order('weight_loss_percentage', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'weightLossSpeed':
          query = query
            .order('weight_loss_speed_lbs_per_month', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        case 'weightLossSpeedPercent':
          query = query
            .order('weight_loss_speed_percent_per_month', { ascending: sortOrder === 'asc', nullsFirst: false })
            .order('post_id', { ascending: true })
          break
        default:
          query = query
            .order('created_at', { ascending: false, nullsFirst: false })
            .order('post_id', { ascending: true })
      }

      // Apply pagination AFTER sorting
      query = query.range(offset, offset + input.limit - 1)

      const { data, count, error } = await query

      if (error) {
        console.error('Supabase error:', error)
        throw new Error('Failed to fetch experiences')
      }

      // Map feature_id to id for frontend compatibility
      const mappedData = (data || []).map((experience) => ({
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
