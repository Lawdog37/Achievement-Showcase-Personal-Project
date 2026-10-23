import type { ShowcaseItem } from '../api/types'
import { useShowcase } from '../hooks/usePlayerData'
import { formatDate } from '../lib/format'
import { rarityTier } from '../lib/rarity'
import { ErrorBlock, LoadingBlock } from './Status'

function AchievementCard({ item }: { item: ShowcaseItem }) {
  const tier = rarityTier(item.global_percent)
  return (
    <article className={`flex gap-3 rounded-xl border p-3 ${tier.className}`}>
      {item.icon_url && (
        <img src={item.icon_url} alt="" loading="lazy" className="size-16 shrink-0 rounded-md" />
      )}
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide">
          {tier.label} · {item.global_percent.toFixed(1)}%
        </p>
        <h3 className="truncate font-semibold text-slate-100">{item.display_name}</h3>
        <p className="truncate text-sm text-slate-400">{item.game_name}</p>
        {item.description && (
          <p className="mt-1 line-clamp-2 text-xs text-slate-400">{item.description}</p>
        )}
        {item.unlocked_at && (
          <p className="mt-1 text-xs text-slate-500">Unlocked {formatDate(item.unlocked_at)}</p>
        )}
      </div>
    </article>
  )
}

export function ShowcaseGrid({ steamId }: { steamId: string }) {
  const { data, isPending, error } = useShowcase(steamId)
  if (isPending) return <LoadingBlock label="Loading showcase…" />
  if (error) return <ErrorBlock message={error.message} />
  if (data.length === 0) return <p className="text-slate-400">No achievements unlocked yet.</p>

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((item) => (
        <AchievementCard key={`${item.app_id}-${item.api_name}`} item={item} />
      ))}
    </div>
  )
}