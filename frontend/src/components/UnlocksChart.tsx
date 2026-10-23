import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useStats } from '../hooks/usePlayerData'
import { ErrorBlock, LoadingBlock } from './Status'

export function UnlocksChart({ steamId }: { steamId: string }) {
  // Same query as StatTiles: TanStack Query fetches it once and shares it
  const { data, isPending, error } = useStats(steamId)
  if (isPending) return <LoadingBlock label="Loading chart…" />
  if (error) return <ErrorBlock message={error.message} />

  return (
    <div className="h-72 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data.unlocks_by_month}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 12 }} minTickGap={24} />
          <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 12 }} width={36} />
          <Tooltip
            cursor={{ fill: '#1e293b' }}
            contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }}
            labelStyle={{ color: '#e2e8f0' }}
          />
          <Bar dataKey="count" name="Unlocks" fill="#38bdf8" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
