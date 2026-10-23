import { useStats } from '../hooks/usePlayerData'
import { formatNumber } from '../lib/format'
import { ErrorBlock, LoadingBlock } from './Status'

export function StatTiles({ steamId }: { steamId: string }) {
  const { data, isPending, error } = useStats(steamId)
  if (isPending) return <LoadingBlock label="Loading stats…" />
  if (error) return <ErrorBlock message={error.message} />

  const tiles = [
    {
      label: 'Achievements',
      value: formatNumber(data.achievements_unlocked),
      detail: `of ${formatNumber(data.achievements_total)}`,
    },
    { label: 'Average completion', value: `${data.average_completion}%`, detail: 'across started games' },
    { label: 'Perfect games', value: formatNumber(data.perfect_games), detail: 'at 100%' },
    {
      label: 'Games started',
      value: formatNumber(data.games_started),
      detail: `of ${formatNumber(data.games_with_achievements)} with achievements`,
    },
    { label: 'Games owned', value: formatNumber(data.games_owned), detail: 'in the library' },
    { label: 'Hours played', value: formatNumber(Math.round(data.hours_played)), detail: 'all time' },
  ]

  return (
    <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {tiles.map((tile) => (
        <div key={tile.label} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-400">{tile.label}</p>
          <p className="mt-1 text-2xl font-bold">{tile.value}</p>
          <p className="text-xs text-slate-500">{tile.detail}</p>
        </div>
      ))}
    </div>
  )
}