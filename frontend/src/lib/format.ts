const numberFormat = new Intl.NumberFormat()

/** 4891 -> "4,891" (uses the visitor's own number style) */
export const formatNumber = (n: number) => numberFormat.format(n)

/** ISO time -> "Jun 21, 2024" in the visitor's own time zone */
export function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
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
