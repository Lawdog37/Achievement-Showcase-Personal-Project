// Remembers the last player you viewed, in the browser's localStorage.
// It's only a convenience: if storage is blocked or empty, nothing breaks.

export interface RememberedPlayer {
  steamId: string
  name: string
  avatarUrl: string | null
}

/** The two methods we need from localStorage. Tests pass in a fake one. */
export interface KeyValueStore {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
}

const KEY = 'achievement-showcase:last-player'

function browserStorage(): KeyValueStore | null {
  try {
    return globalThis.localStorage ?? null
  } catch {
    return null // some privacy settings block storage entirely
  }
}

export function rememberPlayer(player: RememberedPlayer, storage = browserStorage()) {
  try {
    storage?.setItem(KEY, JSON.stringify(player))
  } catch {
    // Storage full or blocked: not important, skip it
  }
}

export function recallPlayer(storage = browserStorage()): RememberedPlayer | null {
  try {
    const saved = JSON.parse(storage?.getItem(KEY) ?? 'null')
    // Anything could be in storage, so check it looks right before trusting it
    if (typeof saved?.steamId === 'string' && /^\d{17}$/.test(saved.steamId)) {
      return saved as RememberedPlayer
    }
  } catch {
    // Not valid JSON: ignore it
  }
  return null
}
