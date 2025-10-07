import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'

dotenv.config({ path: '../../.env' })

const supabaseUrl = process.env.SUPABASE_URL!
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY!
const supabase = createClient(supabaseUrl, supabaseKey)

async function investigateDuplicates() {
  console.log('Investigating why we have duplicate post_ids...\n')

  // Get one example duplicate post
  const { data } = await supabase
    .from('mv_experiences_denormalized')
    .select('*')
    .is('comment_id', null)
    .eq('post_id', '1i9lz9h')

  if (data && data.length > 1) {
    console.log(`Found ${data.length} rows for post_id '1i9lz9h':\n`)

    data.forEach((row, index) => {
      console.log(`Row ${index + 1}:`)
      console.log(`  feature_id: ${row.feature_id}`)
      console.log(`  post_id: ${row.post_id}`)
      console.log(`  comment_id: ${row.comment_id}`)
      console.log(`  primary_drug: ${row.primary_drug}`)
      console.log(`  created_at: ${row.created_at}`)
      console.log(`  summary: ${row.summary?.substring(0, 100)}...`)
      console.log()
    })

    // Check if they differ in any significant way
    const firstRow = data[0]
    const differences: string[] = []

    for (let i = 1; i < data.length; i++) {
      const currentRow = data[i]
      Object.keys(firstRow).forEach(key => {
        if (JSON.stringify(firstRow[key]) !== JSON.stringify(currentRow[key])) {
          if (!differences.includes(key)) {
            differences.push(key)
          }
        }
      })
    }

    console.log('Fields that differ between rows:', differences.length > 0 ? differences : ['None - rows are identical!'])
  }

  // Check the underlying extracted_features table
  console.log('\n=== Checking extracted_features table ===')
  const { data: features } = await supabase
    .from('extracted_features')
    .select('id, post_id, comment_id, primary_drug')
    .eq('post_id', '1i9lz9h')
    .is('comment_id', null)

  if (features) {
    console.log(`Found ${features.length} feature rows with post_id='1i9lz9h' and comment_id IS NULL:`)
    features.forEach(f => {
      console.log(`  id: ${f.id}, post_id: ${f.post_id}, comment_id: ${f.comment_id}, drug: ${f.primary_drug}`)
    })
  }
}

investigateDuplicates().catch(console.error)
