'use client'

import { useState, type ReactNode } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'
import { DemoBanner } from '@/components/layout/DemoBanner'

export function AppShell({ children }: { children: ReactNode }) {
  const [navOpen, setNavOpen] = useState(false)
  return (
    <div className="app-canvas relative flex min-h-screen text-slate-200">
      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <TopBar onOpenNav={() => setNavOpen(true)} />
        <DemoBanner />
        <main className="flex-1 overflow-x-hidden p-4 md:p-6 lg:p-8">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  )
}
