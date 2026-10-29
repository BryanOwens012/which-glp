import { createClient } from '@supabase/supabase-js'
import { parseSupabaseSecretKey } from './config.js'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = parseSupabaseSecretKey(process.env.SUPABASE_SECRET_KEY)

if (!supabaseUrl) {
  throw new Error('Missing SUPABASE_URL environment variable')
}

export const supabase = createClient(supabaseUrl, supabaseKey)
