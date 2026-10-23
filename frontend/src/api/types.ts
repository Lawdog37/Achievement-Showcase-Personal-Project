// These mirror backend/app/schemas.py. If you change one, change the other.
// Times arrive as ISO text, like "2024-06-21T18:03:11Z".

export interface Player {
  steam_id: string
  name: string
  avatar_url: string | null
  last_synced_at: string | null
}

export interface ShowcaseItem {
  app_id: number
  game_name: string
  api_name: string
  display_name: string
  description: string | null
  icon_url: string | null
  global_percent: number
  unlocked_at: string | null
}

export interface GameProgress {
  app_id: number
  name: string
  icon_url: string | null
  unlocked: number
  total: number
  pct: number
}

export interface LockedAchievement {
  app_id: number
  game_name: string
  api_name: string
  display_name: string
  description: string | null
  icon_gray_url: string | null
  global_percent: number
}

export interface InProgress {
  games: GameProgress[]
  next_easiest: LockedAchievement[]
}

export interface Stats {
  games_owned: number
  games_with_achievements: number
  games_started: number
  perfect_games: number
  achievements_unlocked: number
  achievements_total: number
  average_completion: number
  hours_played: number
  unlocks_by_month: { month: string; count: number }[]
}

export type SyncState = 'idle' | 'running' | 'done' | 'failed'

export interface SyncStatus {
  steam_id: string
  state: SyncState
  started_at: string | null
  finished_at: string | null
  result: { games: number; synced: number; skipped: number; failed: number; seconds: number } | null
  error: string | null
}