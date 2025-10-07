import { router } from '../lib/trpc.js'
import { platformRouter } from './platform.js'
import { drugsRouter } from './drugs.js'
import { experiencesRouter } from './experiences.js'
import { locationsRouter } from './locations.js'
import { demographicsRouter } from './demographics.js'

export const appRouter = router({
  platform: platformRouter,
  drugs: drugsRouter,
  experiences: experiencesRouter,
  locations: locationsRouter,
  demographics: demographicsRouter,
})

export type AppRouter = typeof appRouter
