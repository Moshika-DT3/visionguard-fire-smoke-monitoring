import { Link, NavLink, Outlet } from 'react-router'
import { cx } from './styles'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/cameras', label: 'Camera Sources' },
  { to: '/video-testing', label: 'Video Testing' },
  { to: '/incidents', label: 'Incident History' },
  { to: '/status', label: 'System Status' },
]

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas leading-normal text-ink">
      <header className="flex min-h-18.5 flex-col items-start justify-between gap-6 bg-navy px-[clamp(1rem,5vw,5rem)] py-3 text-white sm:flex-row sm:items-center">
        <Link className="inline-flex items-center gap-3 text-inherit no-underline" to="/" aria-label="VisionGuard dashboard">
          <span aria-hidden="true" className="grid size-9.5 place-items-center rounded-[10px] bg-brand text-[0.8rem] font-extrabold">
            VG
          </span>
          <span>
            <strong className="block">VisionGuard</strong>
            <small className="block text-[0.7rem] text-[#b8c5da]">Fire &amp; Smoke Monitoring</small>
          </span>
        </Link>
        <nav aria-label="Primary navigation" className="flex w-full flex-wrap gap-x-4.5 gap-y-1 sm:w-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cx(
                  'text-[0.9rem] no-underline hover:text-white hover:underline focus-visible:text-white focus-visible:underline',
                  isActive ? 'text-white underline decoration-2 underline-offset-[6px]' : 'text-[#dbe6f6]',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-[1320px] flex-1 px-[clamp(1rem,4vw,2rem)] py-[clamp(1.5rem,4vw,3rem)]">
        <Outlet />
      </main>

      <footer className="flex flex-col justify-between gap-4 border-t border-line bg-white px-[clamp(1rem,5vw,5rem)] py-5 text-[0.82rem] text-muted sm:flex-row">
        <span>VisionGuard baseline demo</span>
        <span>Powered by YOLO Detection Provider</span>
      </footer>
    </div>
  )
}
