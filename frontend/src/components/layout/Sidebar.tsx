'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  BellRing,
  BrainCircuit,
  CloudSun,
  FlaskConical,
  History,
  LayoutDashboard,
  LineChart,
  Map as MapIcon,
  RadioTower,
  Sparkles,
  Wind,
  X,
} from 'lucide-react'
import clsx from 'clsx'

interface NavItem {
  href: string
  label: string
  icon: typeof LayoutDashboard
}

const OVERVIEW: NavItem[] = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/map', label: 'Live Map', icon: MapIcon },
]

const ANALYTICS: NavItem[] = [
  { href: '/forecast', label: 'Forecast', icon: LineChart },
  { href: '/stations', label: 'Station Explorer', icon: RadioTower },
  { href: '/analysis', label: 'Weather–Pollution', icon: CloudSun },
  { href: '/history', label: 'Historical Analysis', icon: History },
]

const INTELLIGENCE: NavItem[] = [
  { href: '/models', label: 'Model Intelligence', icon: BrainCircuit },
  { href: '/alerts', label: 'Alerts', icon: BellRing },
  { href: '/research', label: 'Research Mode', icon: FlaskConical },
]

const GROUPS: Array<[string, NavItem[]]> = [
  ['Overview', OVERVIEW],
  ['Analytics', ANALYTICS],
  ['Intelligence', INTELLIGENCE],
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

function NavList({ group, pathname, onClose }: { group: NavItem[]; pathname: string; onClose: () => void }) {
  return (
    <ul className="space-y-1">
      {group.map(({ href, label, icon: Icon }) => {
        const active = href === '/' ? pathname === '/' : pathname.startsWith(href)
        return (
          <li key={href}>
            <Link
              href={href}
              onClick={onClose}
              className={clsx(
                'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all',
                active
                  ? 'bg-emerald-500/10 font-medium text-emerald-300'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200',
              )}
              aria-current={active ? 'page' : undefined}
            >
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-emerald-400 shadow-glow" />
              )}
              <Icon
                size={17}
                className={clsx(
                  'transition-transform group-hover:scale-110',
                  active ? 'text-emerald-300' : 'text-slate-500 group-hover:text-slate-300',
                )}
              />
              {label}
            </Link>
          </li>
        )
      })}
    </ul>
  )
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname()
  return (
    <>
      {open && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800/80 bg-slate-950/70 backdrop-blur-xl transition-transform duration-200 md:static md:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center justify-between border-b border-slate-800/80 px-5 py-4">
          <Link href="/" className="group flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400/25 to-sky-500/20 text-emerald-300 shadow-inner ring-1 ring-inset ring-emerald-400/30">
              <Wind size={19} />
            </span>
            <span>
              <span className="block text-[15px] font-semibold tracking-wide text-slate-50">
                AiraCast
              </span>
              <span className="block text-[10px] uppercase tracking-[0.2em] text-slate-500">
                NCR Environmental Intel
              </span>
            </span>
          </Link>
          <button
            className="rounded p-1 text-slate-500 hover:text-slate-300 md:hidden"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5" aria-label="Main navigation">
          {GROUPS.map(([label, items]) => (
            <div key={label}>
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">
                {label}
              </p>
              <NavList group={items} pathname={pathname} onClose={onClose} />
            </div>
          ))}

          <div className="rounded-xl border border-slate-800/70 bg-gradient-to-br from-emerald-500/8 to-sky-500/8 p-3">
            <div className="flex items-center gap-2 text-xs font-medium text-emerald-300">
              <Sparkles size={14} />
              Coupled model
            </div>
            <p className="mt-1 text-[11px] leading-relaxed text-slate-500">
              Weather-coupled AQI forecasts with uncertainty and explainability, spanning Delhi NCR.
            </p>
          </div>
        </nav>

        <div className="border-t border-slate-800/80 px-5 py-4 text-[11px] leading-relaxed text-slate-600">
          <span className="font-medium text-slate-500">Data sources</span>
          <br />
          CPCB · OpenAQ · Open-Meteo
          <div className="mt-1.5 flex items-center gap-1.5 text-slate-500">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Forecasts: model-derived guidance
          </div>
        </div>
      </aside>
    </>
  )
}
