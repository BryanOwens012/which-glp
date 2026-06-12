import { renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { HOVER_INTENT_DELAY_MS } from '@/lib/prefetch'
import { useHoverPrefetch } from './use-hover-prefetch'

describe('useHoverPrefetch', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('fires after the pointer rests for the delay', () => {
    const onHoverIntent = vi.fn()
    const { result } = renderHook(() => useHoverPrefetch(onHoverIntent))

    result.current('row-1').onMouseEnter()
    vi.advanceTimersByTime(HOVER_INTENT_DELAY_MS - 1)
    expect(onHoverIntent).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(onHoverIntent).toHaveBeenCalledExactlyOnceWith('row-1')
  })

  it('does not fire when the pointer leaves before the delay', () => {
    const onHoverIntent = vi.fn()
    const { result } = renderHook(() => useHoverPrefetch(onHoverIntent))

    const props = result.current('row-1')
    props.onMouseEnter()
    vi.advanceTimersByTime(HOVER_INTENT_DELAY_MS - 1)
    props.onMouseLeave()
    vi.advanceTimersByTime(10_000)
    expect(onHoverIntent).not.toHaveBeenCalled()
  })

  it('a quick sweep across rows fires only for the row the pointer rests on', () => {
    const onHoverIntent = vi.fn()
    const { result } = renderHook(() => useHoverPrefetch(onHoverIntent))

    const row1 = result.current('row-1')
    const row2 = result.current('row-2')
    row1.onMouseEnter()
    vi.advanceTimersByTime(50)
    row1.onMouseLeave()
    row2.onMouseEnter()
    vi.advanceTimersByTime(HOVER_INTENT_DELAY_MS)
    expect(onHoverIntent).toHaveBeenCalledExactlyOnceWith('row-2')
  })

  it('re-entering the same row restarts the timer', () => {
    const onHoverIntent = vi.fn()
    const { result } = renderHook(() => useHoverPrefetch(onHoverIntent))

    const props = result.current('row-1')
    props.onMouseEnter()
    vi.advanceTimersByTime(HOVER_INTENT_DELAY_MS - 1)
    props.onMouseEnter() // re-enter without leave (e.g. child element churn)
    vi.advanceTimersByTime(HOVER_INTENT_DELAY_MS - 1)
    expect(onHoverIntent).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(onHoverIntent).toHaveBeenCalledOnce()
  })

  it('honors a custom delay', () => {
    const onHoverIntent = vi.fn()
    const { result } = renderHook(() => useHoverPrefetch(onHoverIntent, 500))

    result.current('row-1').onMouseEnter()
    vi.advanceTimersByTime(499)
    expect(onHoverIntent).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(onHoverIntent).toHaveBeenCalledOnce()
  })

  it('always calls the latest callback (no stale closures)', () => {
    const first = vi.fn()
    const second = vi.fn()
    const { result, rerender } = renderHook(
      ({ callback }) => useHoverPrefetch(callback),
      { initialProps: { callback: first } }
    )

    result.current('row-1').onMouseEnter()
    rerender({ callback: second })
    vi.advanceTimersByTime(HOVER_INTENT_DELAY_MS)
    expect(first).not.toHaveBeenCalled()
    expect(second).toHaveBeenCalledExactlyOnceWith('row-1')
  })

  it('clears a pending timer on unmount', () => {
    const onHoverIntent = vi.fn()
    const { result, unmount } = renderHook(() => useHoverPrefetch(onHoverIntent))

    result.current('row-1').onMouseEnter()
    unmount()
    vi.advanceTimersByTime(10_000)
    expect(onHoverIntent).not.toHaveBeenCalled()
  })
})
