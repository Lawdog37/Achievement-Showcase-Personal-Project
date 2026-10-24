import { Link } from 'react-router'
import { useHunts } from '../hooks/usePlayerData'
import type { RememberedPlayer } from '../lib/recentPlayer'
import { ProgressBar } from './ProgressBar'

/** "Welcome back" card for the last player viewed, with their top hunts. */
export function WelcomeBack({ player }: { player: RememberedPlayer }) {
  const hunts = useHunts(player.steamId)
  const topHunts = hunts.data?.slice(0, 3) ?? []
  const base = `/player/${player.steamId}`

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center gap-3">
        {player.avatarUrl && <img src={player.avatarUrl} alt="" className="size-10 rounded-lg" />}
        <p className="flex-1">
          Welcome back, <span className="font-semibold">{player.name}</span>
        </p>
        <Link
          to={base}
          className="rounded-lg bg-sky-500 px-3 py-1.5 text-sm font-medium text-slate-950 hover:bg-sky-400"
        >
          Open profile
        </Link>
      </div>

      {topHunts.length > 0 && (
        <div className="mt-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">You're hunting</p>
          <ul className="mt-2 space-y-2">
            {topHunts.map(({ game }) => (
              <li key={game.app_id} className="flex items-center gap-3 text-sm">
                <span className="w-40 truncate sm:w-56">{game.name}</span>
                <div className="flex-1">
                  <ProgressBar percent={game.pct} />
                </div>
                <span className="w-16 text-right text-slate-400">{game.remaining} left</span>
              </li>
            ))}
          </ul>
          <Link to={`${base}/hunting`} className="mt-2 inline-block text-sm text-sky-400">
            See all hunts →
          </Link>
        </div>
      )}
    </section>
  )
}
