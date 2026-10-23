import type { ReactNode } from 'react'

interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="mb-4 flex items-center justify-between gap-4 rounded-xl border border-[#f3c4c4] bg-[#fdf0f0] px-4 py-3 font-bold text-danger"
    >
      <span>{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 cursor-pointer rounded-lg border border-danger bg-white px-3 py-1.5 text-sm text-danger transition-colors hover:bg-danger hover:text-white focus-visible:bg-danger focus-visible:text-white"
        >
          Retry
        </button>
      )}
    </div>
  )
}

export function TableMessageRow({ colSpan, children }: { colSpan: number; children: ReactNode }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-2.5 py-6 text-center text-muted">
        {children}
      </td>
    </tr>
  )
}

/** Loading placeholder; width is a Tailwind width class such as "w-10". */
export function Skeleton({ width = 'w-8' }: { width?: string }) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-[1em] rounded-md bg-line align-middle motion-safe:animate-pulse ${width}`}
    />
  )
}

export function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="mr-2 inline-block size-3.5 rounded-full border-2 border-line border-t-brand align-[-2px] motion-safe:animate-spin"
    />
  )
}
