import type { InProgress, Player, ShowcaseItem, Stats, SyncStatus } from './types'

/** An error from our API, carrying the HTTP status (404, 409, ...). */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail // FastAPI's error text
    } catch {
      // The error body wasn't JSON; keep the generic message
    }
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}

// One function per endpoint. Components never build URLs themselves.
export const api = {
  resolve: (query: string) =>
    request<{ steam_id: string }>(`/resolve?q=${encodeURIComponent(query)}`),
  player: (steamId: string) => request<Player>(`/players/${steamId}`),
  showcase: (steamId: string, limit = 12) =>
    request<ShowcaseItem[]>(`/players/${steamId}/showcase?limit=${limit}`),
  inProgress: (steamId: string) =>
    request<InProgress>(`/players/${steamId}/in-progress?games_limit=8&achievements_limit=8`),
  stats: (steamId: string) => request<Stats>(`/players/${steamId}/stats`),
  syncStatus: (steamId: string) => request<SyncStatus>(`/players/${steamId}/sync`),
  startSync: (steamId: string, force = false) =>
    request<SyncStatus>(`/players/${steamId}/sync?force=${force}`, { method: 'POST' }),
}
