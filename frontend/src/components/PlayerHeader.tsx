import type { Player } from '../api/types'
import { timeAgo } from '../lib/format'
import { SyncPanel } from './SyncPanel'

export function PlayerHeader({ player }: { player: Player }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        {player.avatar_url && (
          <img src={player.avatar_url} alt="" className="size-16 rounded-lg ring-2 ring-slate-700" />
        )}
        <div>
          <h1 className="text-2xl font-bold">{player.name}</h1>
          <p className="text-sm text-slate-400">
            Last synced {timeAgo(player.last_synced_at)} ·{' '}
            <a
              href={`https://steamcommunity.com/profiles/${player.steam_id}`}
              target="_blank"
              rel="noreferrer"
              className="text-sky-400 hover:underline"
            >
              Steam profile
            </a>
          </p>
        </div>
      </div>
      <SyncPanel steamId={player.steam_id} />
    </div>
  )
}