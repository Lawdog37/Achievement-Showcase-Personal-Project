import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { ApiError, api } from '../api/client'
import type { GameSort, GameStatus, SyncState } from '../api/types'

// Every query for one player starts with ['player', steamId], so we can
// refresh all of them at once after a sync.
const playerKey = (steamId: string) => ['player', steamId] as const

/** Who is signed in, or null if nobody is. */
export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      try {
        return await api.me()
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null // not signed in
        throw error
      }
    },
    staleTime: 5 * 60_000,
  })
}

/** True when the signed-in user owns this profile (and so may change it). */
export function useIsOwner(steamId: string) {
  return useMe().data?.steam_id === steamId
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: api.logout,
    onSuccess: () => queryClient.setQueryData(['me'], null),
  })
}

/** Data for the Overview home page (not tied to any player). */
export function useOverview() {
  return useQuery({
    queryKey: ['overview'],
    queryFn: api.overview,
    staleTime: 10 * 60_000, // it only changes once a day, so 10 minutes is plenty fresh
  })
}

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

export function useGames(steamId: string, status: GameStatus, sort: GameSort) {
  return useQuery({
    // status and sort are part of the key, so each combination is cached separately
    queryKey: [...playerKey(steamId), 'games', status, sort],
    queryFn: () => api.games(steamId, status, sort),
    // Keep showing the old list while the new one loads (no flicker when switching tabs)
    placeholderData: keepPreviousData,
  })
}

export function useHunts(steamId: string) {
  return useQuery({
    queryKey: [...playerKey(steamId), 'hunts'],
    queryFn: () => api.hunts(steamId),
  })
}

/** Add, remove and refresh hunts. Each one reloads the player's data when done. */
export function useHuntActions(steamId: string) {
  const queryClient = useQueryClient()
  const onSuccess = () => queryClient.invalidateQueries({ queryKey: playerKey(steamId) })
  return {
    add: useMutation({ mutationFn: (appId: number) => api.addHunt(steamId, appId), onSuccess }),
    remove: useMutation({
      mutationFn: (appId: number) => api.removeHunt(steamId, appId),
      onSuccess,
    }),
    refresh: useMutation({
      mutationFn: (appId: number) => api.refreshHunt(steamId, appId),
      onSuccess,
    }),
  }
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
