/**
 * AppRouter stub for production builds.
 *
 * In production (Vercel), we use this stub to avoid importing backend code.
 * In development, you can optionally import the real types from the backend.
 *
 * This is a necessary compromise for independent frontend/backend deployments.
 */

// Use environment variable to conditionally import real types in development
const isDevelopment = process.env.NODE_ENV === 'development'

// Stub type for production
export type AppRouter = {
  platform: any
  drugs: any
  experiences: any
  locations: any
  demographics: any
}
