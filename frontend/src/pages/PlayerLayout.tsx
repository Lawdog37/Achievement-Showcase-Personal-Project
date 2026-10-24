import { Outlet, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { PlayerHeader } from '../components/PlayerHeader'
import { PlayerNav } from '../components/PlayerNav'
import { ErrorBlock, LoadingBlock } from '../components/Status'
import { SyncPanel } from '../components/SyncPanel'
import { useIsOwner, usePlayer } from '../hooks/usePlayerData'
import { useEffect } from 'react'
import { rememberPlayer } from '../lib/recentPlayer'
import { SignInLink } from '../components/AccountMenu'

/**
 * The frame around every player page: loads the player, shows the header and
 * tabs, then <Outlet /> shows whichever tab's page matches the URL.
 */
export default function PlayerLayout() {
  const { steamId = '' } = useParams() // from the URL: /player/:steamId/...
  const validId = /^\d{17}$/.test(steamId)
  const player = usePlayer(steamId, validId)
  const isOwner = useIsOwner(steamId)
  // Remember who was viewed last, so the Overview page can say "welcome back"
  useEffect(() => {
    if (player.data) {
      const { steam_id, name, avatar_url } = player.data
      rememberPlayer({ steamId: steam_id, name, avatarUrl: avatar_url })
    }
  }, [player.data])

  if (!validId) return <ErrorBlock message="That isn't a valid SteamID." />
  if (player.isPending) return <LoadingBlock label="Loading profile…" />

  if (player.error) {
    if (player.error instanceof ApiError && player.error.status === 404) {
      return (
        <div className="mx-auto max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h1 className="text-xl font-semibold">Not synced yet</h1>
          <p className="mt-2 mb-4 text-slate-400">
            This profile isn't in the database. Sync it to fetch its games and achievements from
            Steam.
          </p>
          {isOwner ? (
            <SyncPanel steamId={steamId} />
          ) : (
            <p className="text-sm text-slate-400">
              Is this your profile? <SignInLink>Sign in through Steam</SignInLink> to sync it.
            </p>
          )}
        </div>
      )
    }
    return <ErrorBlock message={player.error.message} />
  }

  return (
    <>
      <PlayerHeader player={player.data} />
      <PlayerNav />
      <Outlet />
    </>
  )
}
