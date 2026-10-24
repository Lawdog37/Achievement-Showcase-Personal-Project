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

export interface GameCompletion extends GameProgress {
  remaining: number
  playtime_minutes: number
  last_played_at: string | null
}

export type GameStatus = 'in_progress' | 'completed' | 'not_started' | 'all'
export type GameSort = 'percent' | 'remaining' | 'name' | 'recent'

export interface HuntAchievement {
  api_name: string
  display_name: string
  description: string | null
  icon_gray_url: string | null
  hidden: boolean
  global_percent: number | null
}

export interface Hunt {
  game: GameCompletion
  added_at: string
  locked: HuntAchievement[] // easiest first
}

export interface ChartGame {
  rank: number
  last_week_rank: number | null
  peak_players: number
  app_id: number
  name: string
  image_url: string | null
  has_achievements: boolean | null
  rarest_percent: number | null
  achievement_count: number | null
}

export interface TrendingGame {
  app_id: number
  name: string
  image_url: string | null
  rarest_before: number
  rarest_now: number
  change: number
  days: number
}

export interface Overview {
  chart_date: string | null
  most_played: ChartGame[]
  trending: TrendingGame[]
  snapshot_days: number
}

export interface Me {
  steam_id: string
}
