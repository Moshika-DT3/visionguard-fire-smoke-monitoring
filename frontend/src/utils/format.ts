const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** Matches the Jinja format '%b %d, %Y %H:%M UTC'. */
export function formatDetectedAt(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${MONTHS[date.getUTCMonth()]} ${pad(date.getUTCDate())}, ${date.getUTCFullYear()} ${pad(
    date.getUTCHours(),
  )}:${pad(date.getUTCMinutes())} UTC`
}

/** 0.873 -> "87%" */
export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

/** "fire" -> "Fire" */
export function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}
