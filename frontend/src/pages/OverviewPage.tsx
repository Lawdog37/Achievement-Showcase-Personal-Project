import type { ChartGame, TrendingGame } from '../api/types'
import { PlayerSearch } from '../components/PlayerSearch'
import { ErrorBlock, LoadingBlock, Section } from '../components/Status'
import { WelcomeBack } from '../components/WelcomeBack'
import { useOverview } from '../hooks/usePlayerData'
import { formatCompact, formatDate } from '../lib/format'
import { rankChange } from '../lib/ranks'
import { rarityTier } from '../lib/rarity'
import { recallPlayer } from '../lib/recentPlayer'

const TONE_CLASSES = {
  up: 'text-emerald-400',
  down: 'text-rose-400',
  same: 'text-slate-500',
  new: 'text-sky-400',
}

/** How hard a game is to 100%, judged by its rarest achievement. */
function Difficulty({ game }: { game: ChartGame }) {
  if (game.has_achievements === false) {
    return <span className="text-xs text-slate-500">No achievements</span>
  }
  if (game.rarest_percent === null) {
    return <span className="text-xs text-slate-500">Rarity coming soon</span>
  }
  const tier = rarityTier(game.rarest_percent)
  return (
    <span className={`rounded-md border px-2 py-0.5 text-xs ${tier.className}`}>
      Hardest: {game.rarest_percent.toFixed(1)}% · {tier.label}
    </span>
  )
}

function ChartRow({ game }: { game: ChartGame }) {
  const change = rankChange(game.rank, game.last_week_rank)
  return (
    <li className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 p-2 pr-3">
      <span className="w-8 shrink-0 text-center text-lg font-bold text-slate-400">{game.rank}</span>
      {game.image_url ? (
        <img
          src={game.image_url}
          alt=""
          loading="lazy"
          className="hidden h-[43px] w-[115px] shrink-0 rounded object-cover sm:block"
        />
      ) : (
        <div className="hidden h-[43px] w-[115px] shrink-0 rounded bg-slate-800 sm:block" />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{game.name}</p>
        <p className="text-xs text-slate-400">
          {formatCompact(game.peak_players)} players at peak ·{' '}
          <span className={TONE_CLASSES[change.tone]}>{change.label}</span>
          {game.achievement_count
            ? ` · ${game.achievement_count} ${game.achievement_count === 1 ? 'achievement' : 'achievements'}`
            : ''}
        </p>
      </div>
      <div className="shrink-0">
        <Difficulty game={game} />
      </div>
    </li>
  )
}

function TrendingRow({ game }: { game: TrendingGame }) {
  return (
    <li className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 p-3">
      {game.image_url && (
        <img src={game.image_url} alt="" className="h-[43px] w-[115px] rounded object-cover" />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{game.name}</p>
        <p className="text-xs text-slate-400">
          Rarest achievement: {game.rarest_before.toFixed(1)}% → {game.rarest_now.toFixed(1)}% of
          players in {game.days} {game.days === 1 ? 'day' : 'days'}
        </p>
      </div>
      <span className="shrink-0 text-sm font-semibold text-emerald-400">
        +{game.change.toFixed(1)}
      </span>
    </li>
  )
}

export default function OverviewPage() {
  const remembered = recallPlayer()
  const { data, isPending, error } = useOverview()

  return (
    <>
      <div className="mx-auto max-w-xl py-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Show off your rarest achievements</h1>
        <p className="mt-3 mb-6 text-slate-400">
          Enter a Steam profile URL, custom name or SteamID. The profile's game details must be
          public.
        </p>
        <PlayerSearch />
      </div>

      {remembered && <WelcomeBack player={remembered} />}

      {isPending && <LoadingBlock label="Loading what's popular…" />}
      {error && <ErrorBlock message={error.message} />}
      {data && (
        <div className="grid gap-x-8 lg:grid-cols-[3fr_2fr]">
          <Section
            title="Most played on Steam"
            subtitle={
              data.chart_date
                ? `Steam's chart for ${formatDate(data.chart_date)}, and how hard each is to 100%`
                : undefined
            }
          >
            {data.most_played.length === 0 ? (
              <p className="text-slate-400">
                No chart saved yet. Run <code>python -m app.daily</code> in the backend.
              </p>
            ) : (
              <ol className="space-y-2">
                {data.most_played.map((game) => (
                  <ChartRow key={game.app_id} game={game} />
                ))}
              </ol>
            )}
          </Section>

          <Section
            title="Trending toward 100%"
            subtitle="Games where more players are earning the rarest achievement this week"
          >
            {data.snapshot_days < 2 ? (
              <p className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-400">
                Collecting data: {data.snapshot_days} {data.snapshot_days === 1 ? 'day' : 'days'} of
                rarity snapshots so far. Trends appear once there are at least two days to compare.
              </p>
            ) : data.trending.length === 0 ? (
              <p className="text-sm text-slate-400">
                Nothing is trending yet. Check back tomorrow.
              </p>
            ) : (
              <ul className="space-y-2">
                {data.trending.map((game) => (
                  <TrendingRow key={game.app_id} game={game} />
                ))}
              </ul>
            )}
          </Section>
        </div>
      )}
    </>
  )
}
