'use client'

import { AlertTriangle } from 'lucide-react'
import { useDataSourceStatus } from '@/lib/datasource'
import { DEMO_DISCLAIMER } from '@/lib/demo/data'

export function DemoBanner() {
  const { demoActive, liveSeen } = useDataSourceStatus()
  if (!demoActive || liveSeen) return null
  return (
    <div className="flex items-center gap-2 border-b border-amber-500/30 bg-gradient-to-r from-amber-500/15 via-amber-500/10 to-transparent px-4 py-2 text-xs text-amber-300">
      <AlertTriangle size={14} className="shrink-0" />
      <span className="font-semibold">{DEMO_DISCLAIMER}</span>
      <span className="hidden text-amber-400/80 sm:inline">
        Backend API not reachable — synthetic sample dataset is shown everywhere.
      </span>
    </div>
  )
}
