'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'
import { Menu, Moon, Radio, Sun } from 'lucide-react'
import { useDataSourceStatus } from '@/lib/datasource'
import { istDateTime } from '@/lib/format'

const TITLES: Array<[prefix: string, title: string]> = [
  ['/', 'Overview'],
  ['/map', 'Live Map — Delhi NCR'],
  ['/forecast', 'Forecast'],
  ['/stations', 'Station Explorer'],
  ['/analysis', 'Weather–Pollution Analysis'],
  ['/models', 'Model Intelligence'],
  ['/history', 'Historical Analysis'],
  ['/alerts', 'Alerts'],
  ['/research', 'Research Mode'],
]

function pageTitle(pathname: string): string {
  const match = [...TITLES]
    .sort((a, b) => b[0].length - a[0].length)
    .find(([prefix]) => (prefix === '/' ? pathname === '/' : pathname.startsWith(prefix)))
  return match?.[1] ?? 'AiraCast'
}

function useIstClock(): string {
  const [now, setNow] = useState<string>('')
  useEffect(() => {
    const tick = () => setNow(istDateTime(new Date()))
    tick()
    const id = window.setInterval(tick, 30_000)
    return () => window.clearInterval(id)
  }, [])
  return now
}

function useTheme() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  useEffect(() => {
    const stored = window.localStorage.getItem('airacast-theme')
    const initial = stored === 'light' ? 'light' : 'dark'
    setTheme(initial)
    document.documentElement.classList.toggle('dark', initial === 'dark')
  }, [])
  const toggle = () => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark'
      window.localStorage.setItem('airacast-theme', next)
      document.documentElement.classList.toggle('dark', next === 'dark')
      return next
    })
  }
  return { theme, toggle }
}

interface TopBarProps {
  onOpenNav: () => void
}

export function TopBar({ onOpenNav }: TopBarProps) {
  const pathname = usePathname()
  const clock = useIstClock()
  const { demoActive } = useDataSourceStatus()
  const { theme, toggle } = useTheme()

  return (
    <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-800/80 bg-slate-950/60 px-4 py-3.5 backdrop-blur-xl md:px-6">
      <button
        className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-900 hover:text-slate-200 md:hidden"
        onClick={onOpenNav}
        aria-label="Open navigation"
      >
        <Menu size={20} />
      </button>
      <h1 className="min-w-0 flex-1 truncate bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-base font-semibold text-transparent">
        {pageTitle(pathname)}
      </h1>
      <span
        className={clsx(
          'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wider ring-1 ring-inset',
          demoActive
            ? 'bg-amber-500/15 text-amber-300 ring-amber-500/40'
            : 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40',
        )}
        title={
          demoActive
            ? 'Showing labelled demo data because the backend API is unreachable or not configured'
            : 'Connected to the live backend API'
        }
      >
        <Radio size={12} className="animate-pulse" />
        {demoActive ? 'Demo data' : 'Live'}
      </span>
      <span
        className="hidden items-center gap-1.5 text-xs tabular-nums text-slate-500 sm:flex"
        suppressHydrationWarning
      >
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-slate-600" />
        {clock} IST
      </span>
      <button
        onClick={toggle}
        className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-900 hover:text-slate-200"
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
      </button>
    </header>
  )
}
