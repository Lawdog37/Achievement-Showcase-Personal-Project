import { useStartSync, useSyncStatus } from '../hooks/usePlayerData'

export function SyncPanel({ steamId }: { steamId: string }) {
  const status = useSyncStatus(steamId)
  const startSync = useStartSync(steamId)

  const data = status.data
  const running = data?.state === 'running' || startSync.isPending

  let message = ''
  if (running) message = 'Fetching from Steam. Big libraries take a few minutes.'
  else if (data?.state === 'failed') message = data.error ?? 'Sync failed.'
  else if (data?.state === 'done' && data.result) {
    const r = data.result
    message = `Synced ${r.synced} games in ${r.seconds}s (${r.skipped} unchanged)`
    if (r.failed) message += `, ${r.failed} failed`
  } else if (startSync.error) message = startSync.error.message

  return (
    <div className="flex flex-col items-start gap-2 sm:items-end">
      <button
        type="button"
        onClick={() => startSync.mutate(false)}
        disabled={running}
        className="rounded-lg bg-sky-500 px-4 py-2 font-medium text-slate-950 hover:bg-sky-400 disabled:cursor-wait disabled:opacity-60"
      >
        {running ? 'Syncing…' : 'Sync now'}
      </button>
      {message && (
        <p
          className={`max-w-xs text-xs ${data?.state === 'failed' ? 'text-rose-400' : 'text-slate-400'}`}
        >
          {message}
        </p>
      )}
    </div>
  )
}
