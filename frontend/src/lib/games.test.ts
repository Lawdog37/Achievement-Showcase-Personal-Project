import { describe, expect, it } from 'vitest'
import type { GameCompletion } from '../api/types'
import { filterByName } from './games'

function game(name: string): GameCompletion {
  return {
    app_id: 1,
    name,
    icon_url: null,
    unlocked: 1,
    total: 2,
    pct: 50,
    remaining: 1,
    playtime_minutes: 60,
    last_played_at: null,
  }
}

describe('filterByName', () => {
  const games = [game('Sea of Thieves'), game('Splitgate'), game('Skyrim')]

  it('returns everything when the search is empty', () => {
    expect(filterByName(games, '  ')).toHaveLength(3)
  })

  it('ignores capital letters', () => {
    expect(filterByName(games, 'SEA').map((g) => g.name)).toEqual(['Sea of Thieves'])
  })

  it('matches anywhere in the name', () => {
    expect(filterByName(games, 'gate').map((g) => g.name)).toEqual(['Splitgate'])
  })
})
