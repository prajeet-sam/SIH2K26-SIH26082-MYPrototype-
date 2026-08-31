'use client'

import { useState, type ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DataSourceProvider } from '@/lib/datasource'

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            retry: 0,
            refetchOnWindowFocus: false,
          },
        },
      }),
  )
  return (
    <QueryClientProvider client={queryClient}>
      <DataSourceProvider>{children}</DataSourceProvider>
    </QueryClientProvider>
  )
}
