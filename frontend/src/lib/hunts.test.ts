import { describe, expect, it } from 'vitest'
import type { HuntAchievement } from '../api/types'
import { achievementDescription, rarityText } from './hunts'

function achievement(overrides: Partial<HuntAchievement>): HuntAchievement {
  return {
    api_name: 'A',
    display_name: 'An achievement',
    description: null,
    icon_gray_url: null,
    hidden: false,
    global_percent: 10,
    ...overrides,
  }
}

describe('achievementDescription', () => {
  it('uses the description when there is one', () => {
    expect(achievementDescription(achievement({ description: 'Win a game' }))).toBe('Win a game')
  })

  it('explains hidden achievements', () => {
    expect(achievementDescription(achievement({ hidden: true }))).toMatch(/Hidden/)
  })

  it('is empty when there is simply no description', () => {
    expect(achievementDescription(achievement({}))).toBe('')
  })
})

describe('rarityText', () => {
  it('shows one decimal place', () => {
    expect(rarityText(81.84)).toBe('81.8% of players')
  })

  it('never rounds a real achievement down to 0.0%', () => {
    expect(rarityText(0.04)).toBe('under 0.1% of players')
    expect(rarityText(0)).toBe('under 0.1% of players')
  })

  it('handles a missing number', () => {
    expect(rarityText(null)).toBe('Rarity unknown')
  })
})
