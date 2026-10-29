import { afterEach, describe, expect, it, vi } from 'vitest'

describe('recommendations router', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('refuses to load without INTERNAL_API_KEY, so the API cannot boot without it', async () => {
    vi.stubEnv('INTERNAL_API_KEY', '')

    await expect(import('./recommendations.js')).rejects.toThrow('Missing INTERNAL_API_KEY')
  })

  it('loads with a usable INTERNAL_API_KEY', async () => {
    vi.stubEnv('INTERNAL_API_KEY', 'test-internal-key')

    await expect(import('./recommendations.js')).resolves.toHaveProperty('recommendationsRouter')
  })
})
