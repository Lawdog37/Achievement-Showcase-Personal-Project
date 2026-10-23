import { useInProgress } from '../hooks/usePlayerData'
import { ErrorBlock, LoadingBlock } from './Status'

export function InProgress({ steamId }: { steamId: string }) {
  const { data, isPending, error } = useInProgress(steamId)
  if (isPending) return <LoadingBlock label="Loading progress…" />
  if (error) return <ErrorBlock message={error.message} />

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold">Closest to 100%</h3>
        <ul className="mt-3 space-y-3">
          {data.games.map((game) => (
            <li key={game.app_id} className="flex items-center gap-3">
              {game.icon_url && <img src={game.icon_url} alt="" className="size-8 rounded" />}
              <div className="min-w-0 flex-1">
                <div className="flex justify-between gap-2 text-sm">
                  <span className="truncate">{game.name}</span>
                  <span className="shrink-0 text-slate-400">
                    {game.unlocked}/{game.total}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-slate-800">
                  <div
                    className="h-2 rounded-full bg-emerald-400"
                    style={{ width: `${game.pct}%` }}
                  />
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h3 className="font-semibold">Easiest ones you're missing</h3>
        <ul className="mt-3 space-y-3">
          {data.next_easiest.map((a) => (
            <li key={`${a.app_id}-${a.api_name}`} className="flex items-center gap-3">
              {a.icon_gray_url && <img src={a.icon_gray_url} alt="" className="size-8 rounded" />}
              <div className="min-w-0 flex-1 text-sm">
                <p className="truncate">{a.display_name}</p>
                <p className="truncate text-xs text-slate-400">{a.game_name}</p>
              </div>
              <span className="shrink-0 text-xs text-slate-400">
                {a.global_percent.toFixed(1)}% have it
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
