/** A horizontal bar filled to `percent` (0–100). Turns gold at 100%. */
export function ProgressBar({ percent }: { percent: number }) {
  const done = percent >= 100
  return (
    <div className="h-2 rounded-full bg-slate-800" role="progressbar" aria-valuenow={percent}>
      <div
        className={`h-2 rounded-full ${done ? 'bg-amber-400' : 'bg-emerald-400'}`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  )
}
