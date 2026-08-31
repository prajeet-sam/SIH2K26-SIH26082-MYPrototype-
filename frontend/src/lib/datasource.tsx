'use client'

import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { DataSourceKind } from '@/types/api'

interface DataSourceContextValue {
  demoActive: boolean
  liveSeen: boolean
  reportSource: (source: DataSourceKind) => void
}

const DataSourceContext = createContext<DataSourceContextValue>({
  demoActive: true,
  liveSeen: false,
  reportSource: () => undefined,
})

export function DataSourceProvider({ children }: { children: ReactNode }) {
  const [demoActive, setDemoActive] = useState(true)
  const [liveSeen, setLiveSeen] = useState(false)

  const reportSource = useCallback(
    (source: DataSourceKind) => {
      if (source === 'live') {
        setLiveSeen(true)
        setDemoActive(false)
      } else {
        setDemoActive((prev) => (liveSeen ? prev : true))
      }
    },
    [liveSeen],
  )

  const value = useMemo(
    () => ({ demoActive, liveSeen, reportSource }),
    [demoActive, liveSeen, reportSource],
  )
  return <DataSourceContext.Provider value={value}>{children}</DataSourceContext.Provider>
}

export function useDataSourceStatus(): DataSourceContextValue {
  return useContext(DataSourceContext)
}
