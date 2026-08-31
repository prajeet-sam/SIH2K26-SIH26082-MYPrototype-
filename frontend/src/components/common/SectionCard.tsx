import type { ReactNode } from 'react'
import clsx from 'clsx'

interface SectionCardProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}

export function SectionCard({
  title,
  subtitle,
  actions,
  children,
  className,
  bodyClassName,
}: SectionCardProps) {
  return (
    <section
      className={clsx(
        'relative overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/40 shadow-card backdrop-blur',
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/30 to-transparent" />
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/70 px-5 py-3.5">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold text-slate-100">{title}</h2>
          {subtitle && <p className="mt-0.5 truncate text-xs text-slate-500">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      <div className={clsx('px-5 py-4', bodyClassName)}>{children}</div>
    </section>
  )
}
