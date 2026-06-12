import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  buildExperiencesListInput,
  EXPERIENCES_PAGE_SIZE,
  runWhenIdle,
} from './prefetch'
import { SortDirection, SortField } from './sort-types'

describe('buildExperiencesListInput', () => {
  it('returns the default input with no options', () => {
    expect(buildExperiencesListInput()).toEqual({
      drug: undefined,
      search: undefined,
      sortBy: SortField.DATE,
      sortOrder: SortDirection.DESC,
      limit: EXPERIENCES_PAGE_SIZE,
    })
  })

  it('applies overrides while keeping the other defaults', () => {
    expect(
      buildExperiencesListInput({ drug: 'Ozempic', sortOrder: SortDirection.ASC })
    ).toEqual({
      drug: 'Ozempic',
      search: undefined,
      sortBy: SortField.DATE,
      sortOrder: SortDirection.ASC,
      limit: EXPERIENCES_PAGE_SIZE,
    })
  })

  it('produces the same React Query hash whether optional keys are omitted or undefined', () => {
    // React Query's hashKey is JSON.stringify-based, which drops undefined values —
    // this is what makes prefetched inputs hit the same cache entry as page inputs.
    const fromPrefetcher = buildExperiencesListInput()
    const fromPageState = buildExperiencesListInput({ drug: undefined, search: undefined })
    expect(JSON.stringify(fromPrefetcher)).toBe(JSON.stringify(fromPageState))
  })

  it('preserves empty-string search as given (callers must coerce "" themselves)', () => {
    expect(buildExperiencesListInput({ search: '' }).search).toBe('')
  })
})

describe('runWhenIdle', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('uses requestIdleCallback when available', () => {
    const requestIdleCallback = vi.fn((cb: IdleRequestCallback) => {
      cb({} as IdleDeadline)
      return 1
    })
    vi.stubGlobal('requestIdleCallback', requestIdleCallback)

    const callback = vi.fn()
    runWhenIdle(callback)

    expect(requestIdleCallback).toHaveBeenCalledOnce()
    expect(callback).toHaveBeenCalledOnce()
  })

  it('falls back to setTimeout when requestIdleCallback is missing', () => {
    // jsdom (like Safari) has no requestIdleCallback
    expect('requestIdleCallback' in window).toBe(false)

    const callback = vi.fn()
    runWhenIdle(callback, 500)

    expect(callback).not.toHaveBeenCalled()
    vi.advanceTimersByTime(499)
    expect(callback).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(callback).toHaveBeenCalledOnce()
  })
})
