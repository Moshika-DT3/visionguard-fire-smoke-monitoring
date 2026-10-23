/** Joins class names, skipping falsy values. */
export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ')
}

export const buttonClass =
  'inline-flex items-center justify-center rounded-lg bg-brand px-3.5 py-2.5 font-bold text-white no-underline ' +
  'cursor-pointer transition-colors hover:bg-brand-dark focus-visible:bg-brand-dark focus-visible:outline-2 ' +
  'focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-60 ' +
  'disabled:hover:bg-brand'

export const textLinkClass = 'font-bold text-brand no-underline hover:underline focus-visible:underline'
