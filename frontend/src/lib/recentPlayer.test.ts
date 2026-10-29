import { describe, expect, it } from 'vitest'
import { type KeyValueStore, recallPlayer, rememberPlayer, forgetPlayer } from './recentPlayer'

/** A pretend localStorage that just keeps values in a Map. */
function fakeStorage(): KeyValueStore {
  const values = new Map<string, string>()
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => void values.set(key, value),
    removeItem: (key) => void values.delete(key),
  }
}

const PLAYER = { steamId: '76561198000000001', name: 'Tester', avatarUrl: null }

describe('recent player', () => {
  it('remembers and recalls a player', () => {
    const storage = fakeStorage()
    rememberPlayer(PLAYER, storage)
    expect(recallPlayer(storage)).toEqual(PLAYER)
  })

  it('returns null when nothing is saved', () => {
    expect(recallPlayer(fakeStorage())).toBeNull()
  })

  it('ignores junk in storage', () => {
    const storage = fakeStorage()
    storage.setItem('achievement-showcase:last-player', '{not json')
    expect(recallPlayer(storage)).toBeNull()
    storage.setItem('achievement-showcase:last-player', '{"steamId": "<script>"}')
    expect(recallPlayer(storage)).toBeNull()
  })

  it('copes with no storage at all', () => {
    expect(recallPlayer(null)).toBeNull()
    expect(() => rememberPlayer(PLAYER, null)).not.toThrow()
  })

  it('forgets a player', () => {
    const storage = fakeStorage()
    rememberPlayer(PLAYER, storage)
    forgetPlayer(storage)
    expect(recallPlayer(storage)).toBeNull()
  })
})
