import { describe, expect, it } from 'vitest'
import { rankChange } from './ranks'

describe('rankChange', () => {
  it('shows a climb', () => {
    expect(rankChange(7, 32)).toEqual({ label: '▲ 25', tone: 'up' })
  })

  it('shows a drop', () => {
    expect(rankChange(9, 6)).toEqual({ label: '▼ 3', tone: 'down' })
  })

  it('shows no change', () => {
    expect(rankChange(1, 1).tone).toBe('same')
  })

  it('marks games that were not on last week’s chart as new', () => {
    expect(rankChange(4, null).label).toBe('New')
    expect(rankChange(4, 0).label).toBe('New')
  })
})
