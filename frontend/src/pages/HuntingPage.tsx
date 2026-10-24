import { useState } from 'react'
import { Link, useParams } from 'react-router'
import type { Hunt } from '../api/types'
import { ProgressBar } from '../components/ProgressBar'
import { ErrorBlock, LoadingBlock } from '../components/Status'
import { useHuntActions, useHunts } from '../hooks/usePlayerData'
import { timeAgo } from '../lib/format'
import { achievementDescription, rarityText } from '../lib/hunts'
import { rarityTier } from '../lib/rarity'

const PREVIEW_COUNT = 8 // locked achievements shown before "Show all"

function HuntCard({ hunt, steamId }: { hunt: Hunt; steamId: string }) {
  const { game, locked } = hunt
  const { remove, refresh } = useHuntActions(steamId)
  const [showAll, setShowAll] = useState(false)
  const visible = showAll ? locked : locked.slice(0, PREVIEW_COUNT)
  const refreshing = refresh.isPending && refresh.variables === game.app_id

  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        {game.icon_url && <img src={game.icon_url} alt="" className="size-12 rounded" />}
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-semibold">{game.name}</h2>
          <p className="text-sm text-slate-400">
            {game.unlocked}/{game.total} · {game.pct.toFixed(1)}% · hunting since{' '}
            {timeAgo(hunt.added_at)}
          </p>
          <div className="mt-2">
            <ProgressBar percent={game.pct} />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => refresh.mutate(game.app_id)}
            disabled={refreshing}
            title="Fetch this game's latest achievements from Steam"
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm hover:border-slate-500 disabled:opacity-50"
          >
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
          <button
            type="button"
            onClick={() => remove.mutate(game.app_id)}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-400 hover:border-rose-500/60 hover:text-rose-300"
          >
            Stop hunting
          </button>
        </div>
      </div>
      {refresh.error && <p className="mt-2 text-sm text-rose-400">{refresh.error.message}</p>}

      {locked.length === 0 ? (
        <p className="mt-4 text-amber-300">Every achievement unlocked. Congratulations!</p>
      ) : (
        <>
          <h3 className="mt-4 text-sm font-semibold text-slate-300">
            {locked.length} left, easiest first
          </h3>
          <ul className="mt-2 divide-y divide-slate-800">
            {visible.map((a) => {
              const tier = a.global_percent === null ? null : rarityTier(a.global_percent)
              return (
                <li key={a.api_name} className="flex items-center gap-3 py-2">
                  {a.icon_gray_url && (
                    <img src={a.icon_gray_url} alt="" loading="lazy" className="size-10 rounded" />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{a.display_name}</p>
                    <p className="line-clamp-2 text-xs text-slate-400">
                      {achievementDescription(a)}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-md border px-2 py-0.5 text-xs ${
                      tier?.className ?? 'border-slate-700 text-slate-400'
                    }`}
                  >
                    {tier ? `${tier.label} · ` : ''}
                    {rarityText(a.global_percent)}
                  </span>
                </li>
              )
            })}
          </ul>
          {locked.length > PREVIEW_COUNT && (
            <button
              type="button"
              onClick={() => setShowAll(!showAll)}
              className="mt-2 text-sm text-sky-400 hover:underline"
            >
              {showAll ? 'Show fewer' : `Show all ${locked.length}`}
            </button>
          )}
        </>
      )}
    </article>
  )
}

export default function HuntingPage() {
  const { steamId = '' } = useParams()
  const { data, isPending, error } = useHunts(steamId)

  if (isPending) return <LoadingBlock label="Loading your hunts…" />
  if (error) return <ErrorBlock message={error.message} />

  if (data.length === 0) {
    return (
      <div className="mt-6 rounded-xl border border-dashed border-slate-700 p-8 text-center">
        <p className="text-lg font-semibold">You're not hunting any games yet</p>
        <p className="mt-2 text-slate-400">
          Pick the games you're going for on the{' '}
          <Link to="../near-completion" className="text-sky-400 hover:underline">
            Near completion
          </Link>{' '}
          tab with the <span className="text-slate-200">☆ Hunt</span> button.
        </p>
      </div>
    )
  }

  return (
    <div className="mt-6 space-y-4">
      {data.map((hunt) => (
        <HuntCard key={hunt.game.app_id} hunt={hunt} steamId={steamId} />
      ))}
    </div>
  )
}
