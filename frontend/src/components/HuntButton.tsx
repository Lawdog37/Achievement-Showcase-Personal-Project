import { useHuntActions } from '../hooks/usePlayerData'

/** A star toggle: click to start hunting a game, click again to stop. */
export function HuntButton({
  steamId,
  appId,
  hunted,
}: {
  steamId: string
  appId: number
  hunted: boolean
}) {
  const { add, remove } = useHuntActions(steamId)
  const busy = add.isPending || remove.isPending

  return (
    <button
      type="button"
      onClick={() => (hunted ? remove.mutate(appId) : add.mutate(appId))}
      disabled={busy}
      aria-pressed={hunted}
      title={hunted ? 'Stop hunting this game' : 'Start hunting this game'}
      className={`shrink-0 rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50 ${
        hunted
          ? 'border-amber-400/60 bg-amber-400/10 text-amber-300'
          : 'border-slate-700 text-slate-300 hover:border-slate-500'
      }`}
    >
      {hunted ? '★ Hunting' : '☆ Hunt'}
    </button>
  )
}
