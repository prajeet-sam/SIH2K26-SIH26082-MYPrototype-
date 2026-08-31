'use client'

import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import type { ApiResult } from '@/lib/api'
import { useDataSourceStatus } from '@/lib/datasource'

export function useEnvQuery<T>(
  key: readonly unknown[],
  fetcher: () => Promise<ApiResult<T>>,
  enabled = true,
): UseQueryResult<ApiResult<T>> & { source: DataSourceKindSafe } {
  const { reportSource } = useDataSourceStatus()
  const query = useQuery({
    queryKey: key,
    queryFn: async () => {
      const result = await fetcher()
      reportSource(result.source)
      return result
    },
    enabled,
    staleTime: 60_000,
    retry: 0,
    refetchOnWindowFocus: false,
  })
  return { ...query, source: (query.data?.source ?? null) as DataSourceKindSafe }
}

type DataSourceKindSafe = 'live' | 'demo' | null

export interface EnvQueryView<T> {
  data: T | undefined
  source: DataSourceKindSafe
  isLoading: boolean
  isError: boolean
  refetch: () => void
}

export function toView<T>(q: UseQueryResult<ApiResult<T>>): EnvQueryView<T> {
  return {
    data: q.data?.data,
    source: q.data?.source ?? null,
    isLoading: q.isLoading,
    isError: q.isError,
    refetch: () => void q.refetch(),
  }
}
