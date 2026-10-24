import { useParams } from 'react-router'
import { InProgress } from '../components/InProgress'
import { ShowcaseGrid } from '../components/ShowcaseGrid'
import { StatTiles } from '../components/StatTiles'
import { Section } from '../components/Status'
import { UnlocksChart } from '../components/UnlocksChart'

/** The "Profile" tab: the dashboard from Phase 5, minus the header. */
export default function ProfilePage() {
  const { steamId = '' } = useParams()
  return (
    <>
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
