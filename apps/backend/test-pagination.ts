import { createClient } from '@supabase/supabase-js'
import * as dotenv from 'dotenv'

// Load environment variables
dotenv.config({ path: '../../.env' })

const supabaseUrl = process.env.SUPABASE_URL!
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY!

const supabase = createClient(supabaseUrl, supabaseKey)

async function testPagination() {
  console.log('Testing pagination with date sorting (newest first)...\n')

  // Page 1
  const page1 = await supabase
    .from('mv_experiences_denormalized')
    .select('post_id, created_at, primary_drug, summary')
    .is('comment_id', null)
    .order('created_at', { ascending: false, nullsFirst: false })
    .order('post_id', { ascending: true })
    .range(0, 19)

  console.log('=== PAGE 1 (offset 0-19) ===')
  if (page1.data) {
    console.log(`First: ${page1.data[0]?.created_at} - ${page1.data[0]?.post_id}`)
    console.log(`Last:  ${page1.data[page1.data.length - 1]?.created_at} - ${page1.data[page1.data.length - 1]?.post_id}`)
    console.log(`Count: ${page1.data.length}`)
  }
  console.log()

  // Page 2
  const page2 = await supabase
    .from('mv_experiences_denormalized')
    .select('post_id, created_at, primary_drug, summary')
    .is('comment_id', null)
    .order('created_at', { ascending: false, nullsFirst: false })
    .order('post_id', { ascending: true })
    .range(20, 39)

  console.log('=== PAGE 2 (offset 20-39) ===')
  if (page2.data) {
    console.log(`First: ${page2.data[0]?.created_at} - ${page2.data[0]?.post_id}`)
    console.log(`Last:  ${page2.data[page2.data.length - 1]?.created_at} - ${page2.data[page2.data.length - 1]?.post_id}`)
    console.log(`Count: ${page2.data.length}`)
  }
  console.log()

  // Check for ordering issue
  if (page1.data && page2.data && page1.data.length > 0 && page2.data.length > 0) {
    const lastPage1Date = new Date(page1.data[page1.data.length - 1].created_at!)
    const firstPage2Date = new Date(page2.data[0].created_at!)

    console.log('=== ORDERING CHECK ===')
    console.log(`Last item of page 1: ${lastPage1Date.toISOString()}`)
    console.log(`First item of page 2: ${firstPage2Date.toISOString()}`)

    if (firstPage2Date > lastPage1Date) {
      console.log('❌ ERROR: Page 2 first item is NEWER than Page 1 last item!')
      console.log('This indicates a pagination ordering problem.\n')

      // Check if there are duplicates
      console.log('=== CHECKING FOR DUPLICATE post_ids ===')
      const allPostIds = [...page1.data, ...page2.data].map(r => r.post_id)
      const uniquePostIds = new Set(allPostIds)

      if (allPostIds.length !== uniquePostIds.size) {
        console.log('❌ Found duplicate post_ids across pages!')
        const duplicates = allPostIds.filter((id, index) => allPostIds.indexOf(id) !== index)
        console.log('Duplicates:', duplicates)
      } else {
        console.log('✅ No duplicate post_ids found')
      }
    } else {
      console.log('✅ Ordering is correct')
    }
  }

  console.log('\n=== CHECKING VIEW FOR DUPLICATES ===')
  // Check if the view has duplicate post_ids
  const allData = await supabase
    .from('mv_experiences_denormalized')
    .select('post_id')
    .is('comment_id', null)

  if (allData.data) {
    const postIds = allData.data.map(r => r.post_id)
    const uniquePostIds = new Set(postIds)

    console.log(`Total rows with comment_id IS NULL: ${postIds.length}`)
    console.log(`Unique post_ids: ${uniquePostIds.size}`)

    if (postIds.length !== uniquePostIds.size) {
      console.log('❌ The view has duplicate post_ids even with comment_id IS NULL filter!')

      // Find which post_ids are duplicated
      const counts = new Map<string, number>()
      postIds.forEach(id => counts.set(id, (counts.get(id) || 0) + 1))
      const duplicates = Array.from(counts.entries())
        .filter(([_, count]) => count > 1)
        .slice(0, 5)

      console.log('Sample duplicates:')
      duplicates.forEach(([postId, count]) => {
        console.log(`  ${postId}: ${count} occurrences`)
      })
    } else {
      console.log('✅ No duplicate post_ids in the view')
    }
  }
}

testPagination().catch(console.error)
