import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router'
import type { GameCompletion, GameSort, GameStatus } from '../api/types'
import { HuntButton } from '../components/HuntButton'
import { ProgressBar } from '../components/ProgressBar'
import { ErrorBlock, LoadingBlock } from '../components/Status'
import { useGames, useHunts } from '../hooks/usePlayerData'
import { timeAgo } from '../lib/format'
import { filterByName } from '../lib/games'

const STATUSES: { value: GameStatus; label: string }[] = [
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'not_started', label: 'Not started' },
  { value: 'all', label: 'All' },
]

const SORTS: { value: GameSort; label: string }[] = [
  { value: 'percent', label: 'Closest to 100%' },
  { value: 'remaining', label: 'Fewest left' },
  { value: 'recent', label: 'Recently played' },
  { value: 'name', label: 'Name' },
]

function GameRow({
  game,
  steamId,
  hunted,
}: {
  game: GameCompletion
  steamId: string
  hunted: boolean
}) {
  return (
    <li className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 p-3">
      {game.icon_url && <img src={game.icon_url} alt="" className="size-10 shrink-0 rounded" />}
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <span className="truncate font-medium">{game.name}</span>
          <span className="shrink-0 text-sm text-slate-400">
            {game.unlocked}/{game.total} · {game.pct.toFixed(1)}%
          </span>
        </div>
        <div className="mt-2">
          <ProgressBar percent={game.pct} />
        </div>
        <p className="mt-1 text-xs text-slate-500">
          {game.remaining === 0 ? 'Complete!' : `${game.remaining} left`} · last played{' '}
          {timeAgo(game.last_played_at)}
        </p>
      </div>
      {game.remaining > 0 && <HuntButton steamId={steamId} appId={game.app_id} hunted={hunted} />}
    </li>
  )
}

export default function NearCompletionPage() {
  const { steamId = '' } = useParams()
  // Filter and sort live in the URL (?status=...&sort=...), so the page can be
  // bookmarked or shared, and the Back button works.
  const [params, setParams] = useSearchParams()
  const status = (params.get('status') ?? 'in_progress') as GameStatus
  const sort = (params.get('sort') ?? 'percent') as GameSort
  const [search, setSearch] = useState('')

  const { data, isPending, error, isPlaceholderData } = useGames(steamId, status, sort)
  const hunts = useHunts(steamId)
  const huntedIds = new Set(hunts.data?.map((hunt) => hunt.game.app_id))

  function update(key: string, value: string) {
    const next = new URLSearchParams(params)
    next.set(key, value)
    setParams(next)
  }

  const games = data ? filterByName(data, search) : []

  return (
    <div className="mt-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <button
              key={s.value}
              type="button"
              onClick={() => update('status', s.value)}
              className={`rounded-full px-3 py-1 text-sm ${
                status === s.value
                  ? 'bg-sky-500 text-slate-950'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search games"
            aria-label="Search games"
            className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm outline-none focus:border-sky-400"
          />
          <select
            value={sort}
            onChange={(event) => update('sort', event.target.value)}
            aria-label="Sort games"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm"
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {isPending && <LoadingBlock label="Loading games…" />}
      {error && <ErrorBlock message={error.message} />}
      {data && (
        <>
          <p className="mt-4 text-sm text-slate-400">
            {games.length} {games.length === 1 ? 'game' : 'games'}
          </p>
          {/* Fade the old list slightly while the new filter loads */}
          <ul className={`mt-2 space-y-2 ${isPlaceholderData ? 'opacity-60' : ''}`}>
            {games.map((game) => (
              <GameRow
                key={game.app_id}
                game={game}
                steamId={steamId}
                hunted={huntedIds.has(game.app_id)}
              />
            ))}
          </ul>
          {games.length === 0 && <p className="mt-4 text-slate-400">No games match.</p>}
        </>
      )}
    </div>
  )
}
