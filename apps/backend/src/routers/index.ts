import { router } from '../lib/trpc'
import { platformRouter } from './platform'
import { drugsRouter } from './drugs'
import { experiencesRouter } from './experiences'
import { locationsRouter } from './locations'
import { demographicsRouter } from './demographics'

export const appRouter = router({
  platform: platformRouter,
  drugs: drugsRouter,
  experiences: experiencesRouter,
  locations: locationsRouter,
  demographics: demographicsRouter,
})

export type AppRouter = typeof appRouter
