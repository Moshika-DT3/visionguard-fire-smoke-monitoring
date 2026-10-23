import type { ComponentPropsWithoutRef, ReactNode } from 'react'
import { cx } from './styles'

export function Panel({ className, ...props }: ComponentPropsWithoutRef<'article'>) {
  return (
    <article
      className={cx('rounded-2xl border border-line bg-white p-5 shadow-[0_3px_14px_rgb(25_37_59/0.04)]', className)}
      {...props}
    />
  )
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="mb-1.5 text-xs font-extrabold tracking-[0.08em] text-brand uppercase">{children}</p>
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-4 text-xl font-bold">{children}</h2>
}

export function StatusDot({ tone }: { tone: 'active' | 'offline' | 'idle' }) {
  return (
    <span
      className={cx(
        'inline-block size-2.25 shrink-0 rounded-full',
        tone === 'active' && 'bg-ok ring-3 ring-[#d8f1e6]',
        tone === 'offline' && 'bg-danger ring-3 ring-[#fde3e3]',
        tone === 'idle' && 'bg-muted',
      )}
    />
  )
}

/** Muted secondary line used under table cells. */
export function Subtext({ children }: { children: ReactNode }) {
  return <small className="block text-[0.8rem] text-muted">{children}</small>
}

/* ---- Tables ---- */

export function Table({ caption, children }: { caption: string; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-160 border-collapse">
        <caption className="sr-only">{caption}</caption>
        {children}
      </table>
    </div>
  )
}

export function Th({ children }: { children: ReactNode }) {
  return (
    <th
      scope="col"
      className="border-b border-line px-2.5 py-3.5 text-left text-[0.72rem] font-bold tracking-[0.04em] text-muted uppercase"
    >
      {children}
    </th>
  )
}

export function TBody({ children }: { children: ReactNode }) {
  return <tbody className="[&>tr:last-child>td]:border-b-0">{children}</tbody>
}

export function Td({ children, className }: { children: ReactNode; className?: string }) {
  return <td className={cx('border-b border-line px-2.5 py-3.5 text-left align-middle', className)}>{children}</td>
}

/* ---- Definition lists (status / result panels) ---- */

export function DetailList({ children, className }: { children: ReactNode; className?: string }) {
  return <dl className={cx('m-0 [&>div:last-child]:border-b-0', className)}>{children}</dl>
}

export function DetailRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(105px,1fr)_1.2fr] gap-3 border-b border-line py-3">
      <dt className="text-muted">{label}</dt>
      <dd className="m-0 flex items-center gap-2 font-bold wrap-anywhere">{children}</dd>
    </div>
  )
}
