import type { GameCompletion } from '../api/types'

/** Keep the games whose name contains the search text (ignoring capitals). */
export function filterByName(games: GameCompletion[], search: string) {
  const query = search.trim().toLowerCase()
  if (!query) return games
  return games.filter((game) => game.name.toLowerCase().includes(query))
}
