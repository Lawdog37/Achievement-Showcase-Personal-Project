const numberFormat = new Intl.NumberFormat()

/** 4891 -> "4,891" (uses the visitor's own number style) */
export const formatNumber = (n: number) => numberFormat.format(n)

const compactFormat = new Intl.NumberFormat(undefined, {
  notation: 'compact',
  maximumFractionDigits: 1,
})

/** 1274983 -> "1.3M" */
export const formatCompact = (n: number) => compactFormat.format(n)

/** ISO time -> "Jun 21, 2024" in the visitor's own time zone */
export function formatDate(iso: string) {
  // A date with no time ("2026-10-24") is read as midnight UTC, which is still the
  // day before in the Americas. Add a local midnight so the day stays the same.
  const value = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? `${iso}T00:00:00` : iso
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 31_536_000],
  ['month', 2_592_000],
  ['day', 86_400],
  ['hour', 3_600],
  ['minute', 60],
]

/** ISO time -> "5 minutes ago", "yesterday", ... */
export function timeAgo(iso: string | null) {
  if (!iso) return 'never'
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
  for (const [unit, size] of UNITS) {
    if (seconds >= size) return rtf.format(-Math.floor(seconds / size), unit)
  }
  return 'just now'
}
