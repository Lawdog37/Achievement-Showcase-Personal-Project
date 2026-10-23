export interface RarityTier {
  label: string
  /** Tailwind classes for the card's border, background and label colour */
  className: string
}

/** Turn a global unlock % into a named tier with its own colour. */
export function rarityTier(percent: number): RarityTier {
  if (percent < 1) {
    return { label: 'Legendary', className: 'border-amber-400/60 bg-amber-400/10 text-amber-300' }
  }
  if (percent < 5) {
    return { label: 'Epic', className: 'border-fuchsia-400/50 bg-fuchsia-400/10 text-fuchsia-300' }
  }
  if (percent < 20) {
    return { label: 'Rare', className: 'border-sky-400/50 bg-sky-400/10 text-sky-300' }
  }
  return { label: 'Common', className: 'border-slate-600 bg-slate-800/40 text-slate-300' }
}