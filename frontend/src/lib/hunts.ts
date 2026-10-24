import type { HuntAchievement } from '../api/types'

/** The text to show under an achievement's name. */
export function achievementDescription(achievement: HuntAchievement) {
  if (achievement.description) return achievement.description
  return achievement.hidden ? 'Hidden achievement: Steam keeps the details secret' : ''
}

/** "81.8% of players", "under 0.1% of players", or "Rarity unknown". */
export function rarityText(percent: number | null) {
  if (percent === null) return 'Rarity unknown'
  // Steam rounds to one decimal, so 0.0 really means "fewer than 0.1%"
  if (percent < 0.1) return 'under 0.1% of players'
  return `${percent.toFixed(1)}% of players`
}
