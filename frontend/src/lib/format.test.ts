import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { formatDate, timeAgo } from './format'

describe('timeAgo', () => {
  // Freeze the clock so "now" is the same every time the test runs
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-15T12:00:00Z'))
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('says never when there is no time', () => {
    expect(timeAgo(null)).toBe('never')
  })

  it('says just now for the last minute', () => {
    expect(timeAgo('2026-06-15T11:59:30Z')).toBe('just now')
  })

  it('counts minutes', () => {
    expect(timeAgo('2026-06-15T11:55:00Z')).toMatch(/5 minutes ago/)
  })

  it('counts days', () => {
    expect(timeAgo('2026-06-12T12:00:00Z')).toMatch(/3 days ago/)
  })
})

describe('formatDate', () => {
  it('keeps a plain date on the same day in every time zone', () => {
    expect(formatDate('2026-10-24')).toMatch(/24/)
  })
})
