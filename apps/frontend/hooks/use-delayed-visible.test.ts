import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LOADING_INDICATOR_DELAY_MS, useDelayedVisible } from './use-delayed-visible'

describe('useDelayedVisible', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('stays hidden while inactive', () => {
    const { result } = renderHook(() => useDelayedVisible(false))
    expect(result.current).toBe(false)
    act(() => vi.advanceTimersByTime(10_000))
    expect(result.current).toBe(false)
  })

  it('does not appear before the delay elapses', () => {
    const { result } = renderHook(() => useDelayedVisible(true))
    act(() => vi.advanceTimersByTime(LOADING_INDICATOR_DELAY_MS - 1))
    expect(result.current).toBe(false)
  })

  it('appears once the delay elapses', () => {
    const { result } = renderHook(() => useDelayedVisible(true))
    act(() => vi.advanceTimersByTime(LOADING_INDICATOR_DELAY_MS))
    expect(result.current).toBe(true)
  })

  it('never appears when the load finishes before the delay', () => {
    const { result, rerender } = renderHook(
      ({ isActive }) => useDelayedVisible(isActive),
      { initialProps: { isActive: true } }
    )
    act(() => vi.advanceTimersByTime(LOADING_INDICATOR_DELAY_MS - 50))
    rerender({ isActive: false })
    act(() => vi.advanceTimersByTime(10_000))
    expect(result.current).toBe(false)
  })

  it('resets immediately when deactivated after becoming visible', () => {
    const { result, rerender } = renderHook(
      ({ isActive }) => useDelayedVisible(isActive),
      { initialProps: { isActive: true } }
    )
    act(() => vi.advanceTimersByTime(LOADING_INDICATOR_DELAY_MS))
    expect(result.current).toBe(true)
    rerender({ isActive: false })
    expect(result.current).toBe(false)
  })

  it('honors a custom delay', () => {
    const { result } = renderHook(() => useDelayedVisible(true, 500))
    act(() => vi.advanceTimersByTime(499))
    expect(result.current).toBe(false)
    act(() => vi.advanceTimersByTime(1))
    expect(result.current).toBe(true)
  })

  it('restarts the delay on each new activation', () => {
    const { result, rerender } = renderHook(
      ({ isActive }) => useDelayedVisible(isActive),
      { initialProps: { isActive: true } }
    )
    act(() => vi.advanceTimersByTime(LOADING_INDICATOR_DELAY_MS - 1))
    rerender({ isActive: false })
    rerender({ isActive: true })
    act(() => vi.advanceTimersByTime(LOADING_INDICATOR_DELAY_MS - 1))
    expect(result.current).toBe(false)
    act(() => vi.advanceTimersByTime(1))
    expect(result.current).toBe(true)
  })

  it('cleans up its timer on unmount without firing', () => {
    const { unmount } = renderHook(() => useDelayedVisible(true))
    unmount()
    // Advancing past the delay after unmount must not warn or throw
    act(() => vi.advanceTimersByTime(10_000))
    expect(vi.getTimerCount()).toBe(0)
  })
})
