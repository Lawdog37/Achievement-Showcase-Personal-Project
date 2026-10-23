import { describe, expect, it } from 'vitest'
import { rarityTier } from './rarity'

describe('rarityTier', () => {
  it.each([
    [0.4, 'Legendary'],
    [0.99, 'Legendary'],
    [1, 'Epic'], // exactly 1% is no longer Legendary
    [4.9, 'Epic'],
    [5, 'Rare'],
    [19.9, 'Rare'],
    [20, 'Common'],
    [91, 'Common'],
  ])('%s%% is %s', (percent, label) => {
    expect(rarityTier(percent).label).toBe(label)
  })
})
