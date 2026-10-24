export interface RankChange {
  label: string
  tone: 'up' | 'down' | 'same' | 'new'
}

/** Compare today's chart position with last week's: "▲ 3", "▼ 2", "–" or "New". */
export function rankChange(rank: number, lastWeekRank: number | null): RankChange {
  if (!lastWeekRank) return { label: 'New', tone: 'new' }
  const moved = lastWeekRank - rank // a smaller rank number is better
  if (moved > 0) return { label: `▲ ${moved}`, tone: 'up' }
  if (moved < 0) return { label: `▼ ${-moved}`, tone: 'down' }
  return { label: '–', tone: 'same' }
}
