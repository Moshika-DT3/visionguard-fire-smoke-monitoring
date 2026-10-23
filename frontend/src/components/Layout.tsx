import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router'
import { cx } from './styles'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/cameras', label: 'Camera Sources' },
  { to: '/video-testing', label: 'Video Testing' },
  { to: '/incidents', label: 'Incident History' },
  { to: '/status', label: 'System Status' },
]

function MenuIcon({ open }: { open: boolean }) {
  // Three bars that morph into an X when the menu is open.
  const bar = 'absolute left-0 block h-0.5 w-5 rounded-full bg-current transition-all duration-200 motion-reduce:transition-none'
  return (
    <span aria-hidden="true" className="relative block h-3.5 w-5">
      <span className={cx(bar, open ? 'top-1.5 rotate-45' : 'top-0')} />
      <span className={cx(bar, 'top-1.5', open && 'opacity-0')} />
      <span className={cx(bar, open ? 'top-1.5 -rotate-45' : 'top-3')} />
    </span>
  )
}

export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false)

  // Close the mobile menu with Escape, or when the screen grows to desktop width.
  useEffect(() => {
    if (!menuOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    const desktop = window.matchMedia('(min-width: 64rem)')
    const onResize = () => {
      if (desktop.matches) setMenuOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    desktop.addEventListener('change', onResize)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      desktop.removeEventListener('change', onResize)
    }
  }, [menuOpen])

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cx(
      'no-underline transition-colors',
      // Mobile: full-width rows. Desktop: inline text links.
      'block rounded-lg px-3 py-2.5 text-base lg:rounded-none lg:p-0 lg:text-[0.9rem]',
      'hover:bg-white/10 hover:text-white focus-visible:bg-white/10 focus-visible:text-white',
      'lg:hover:bg-transparent lg:hover:underline lg:focus-visible:bg-transparent lg:focus-visible:underline',
      isActive
        ? 'bg-white/10 font-bold text-white lg:bg-transparent lg:font-normal lg:underline lg:decoration-2 lg:underline-offset-[6px]'
        : 'text-[#dbe6f6]',
    )

  return (
    <div className="flex min-h-screen flex-col bg-canvas leading-normal text-ink">
      <header className="sticky top-0 z-40 bg-navy text-white shadow-[0_2px_10px_rgb(0_0_0/0.15)] lg:static lg:shadow-none">
        <div className="flex min-h-18.5 items-center justify-between gap-6 px-[clamp(1rem,5vw,5rem)] py-3">
          <Link
            className="inline-flex items-center gap-3 text-inherit no-underline"
            to="/"
            aria-label="VisionGuard dashboard"
            onClick={() => setMenuOpen(false)}
          >
            <span
              aria-hidden="true"
              className="grid size-9.5 place-items-center rounded-[10px] bg-brand text-[0.8rem] font-extrabold"
            >
              VG
            </span>
            <span>
              <strong className="block">VisionGuard</strong>
              <small className="block text-[0.7rem] text-[#b8c5da]">Fire &amp; Smoke Monitoring</small>
            </span>
          </Link>

          {/* Desktop navigation */}
          <nav aria-label="Primary navigation" className="hidden gap-x-4.5 lg:flex">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navLinkClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* Mobile menu toggle */}
          <button
            type="button"
            aria-controls="mobile-navigation"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            onClick={() => setMenuOpen((open) => !open)}
            className="grid size-10 cursor-pointer place-items-center rounded-lg text-white transition-colors hover:bg-white/10 focus-visible:bg-white/10 focus-visible:outline-2 focus-visible:outline-white lg:hidden"
          >
            <MenuIcon open={menuOpen} />
          </button>
        </div>

        {/* Mobile navigation panel */}
        <nav
          id="mobile-navigation"
          aria-label="Primary navigation"
          hidden={!menuOpen}
          className="border-t border-white/10 px-[clamp(1rem,5vw,5rem)] pt-2 pb-4 lg:hidden"
        >
          <ul className="m-0 grid list-none gap-1 p-0">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} end={item.end} className={navLinkClass} onClick={() => setMenuOpen(false)}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      {/* Dim the page behind the open mobile menu; tap to close. */}
      {menuOpen && (
        <div
          aria-hidden="true"
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-30 bg-navy/40 lg:hidden"
        />
      )}

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
