import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { ApiError, api } from '../api/client'
import type { SyncState } from '../api/types'

// Every query for one player starts with ['player', steamId], so we can
// refresh all of them at once after a sync.
const playerKey = (steamId: string) => ['player', steamId] as const

export function usePlayer(steamId: string, enabled = true) {
  return useQuery({
    queryKey: [...playerKey(steamId), 'profile'],
    queryFn: () => api.player(steamId),
    enabled,
    // A 404 means "not synced yet", so retrying won't help
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status === 404) && failureCount < 2,
  })
}

export function useShowcase(steamId: string) {
  return useQuery({
    queryKey: [...playerKey(steamId), 'showcase'],
    queryFn: () => api.showcase(steamId),
  })
}

export function useInProgress(steamId: string) {
  return useQuery({
    queryKey: [...playerKey(steamId), 'in-progress'],
    queryFn: () => api.inProgress(steamId),
  })
}

export function useStats(steamId: string) {
  return useQuery({
    queryKey: [...playerKey(steamId), 'stats'],
    queryFn: () => api.stats(steamId),
  })
}

export function useSyncStatus(steamId: string) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['sync', steamId],
    queryFn: () => api.syncStatus(steamId),
    // Ask again every 2 seconds while a sync is running, otherwise stop
    refetchInterval: (q) => (q.state.data?.state === 'running' ? 2000 : false),
  })

  // When a sync goes from "running" to "done", reload the player's data
  const state = query.data?.state
  const previous = useRef<SyncState | undefined>(undefined)
  useEffect(() => {
    if (previous.current === 'running' && state === 'done') {
      queryClient.invalidateQueries({ queryKey: playerKey(steamId) })
    }
    previous.current = state
  }, [state, steamId, queryClient])

  return query
}

export function useStartSync(steamId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (force: boolean) => api.startSync(steamId, force),
    // The answer is the new status ("running"), so store it right away
    onSuccess: (status) => queryClient.setQueryData(['sync', steamId], status),
    // 409 = already running; refresh the status so we start polling it
    onError: () => queryClient.invalidateQueries({ queryKey: ['sync', steamId] }),
  })
}
