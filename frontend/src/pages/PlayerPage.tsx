import { useParams } from 'react-router'
import { ApiError } from '../api/client'
import { InProgress } from '../components/InProgress'
import { PlayerHeader } from '../components/PlayerHeader'
import { ShowcaseGrid } from '../components/ShowcaseGrid'
import { StatTiles } from '../components/StatTiles'
import { ErrorBlock, LoadingBlock, Section } from '../components/Status'
import { SyncPanel } from '../components/SyncPanel'
import { UnlocksChart } from '../components/UnlocksChart'
import { usePlayer } from '../hooks/usePlayerData'

export default function PlayerPage() {
  const { steamId = '' } = useParams() // from the URL: /player/:steamId
  const validId = /^\d{17}$/.test(steamId)
  const player = usePlayer(steamId, validId)

  if (!validId) return <ErrorBlock message="That isn't a valid SteamID." />
  if (player.isPending) return <LoadingBlock label="Loading profile…" />

  if (player.error) {
    if (player.error instanceof ApiError && player.error.status === 404) {
      return (
        <div className="mx-auto max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h1 className="text-xl font-semibold">Not synced yet</h1>
          <p className="mt-2 mb-4 text-slate-400">
            This profile isn't in the database. Sync it to fetch its games and achievements from Steam.
          </p>
          <SyncPanel steamId={steamId} />
        </div>
      )
    }
    return <ErrorBlock message={player.error.message} />
  }

  return (
    <>
      <PlayerHeader player={player.data} />
      <StatTiles steamId={steamId} />
      <Section title="Rarest achievements" subtitle="Unlocked by the fewest players worldwide">
        <ShowcaseGrid steamId={steamId} />
      </Section>
      <Section title="In progress">
        <InProgress steamId={steamId} />
      </Section>
      <Section title="Unlocks over time" subtitle="Achievements unlocked per month">
        <UnlocksChart steamId={steamId} />
      </Section>
    </>
  )
}