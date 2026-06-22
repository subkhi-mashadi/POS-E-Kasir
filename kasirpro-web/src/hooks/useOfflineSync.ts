import { useEffect, useRef } from 'react'
import { useNetworkStatus } from './useNetworkStatus'
import { syncPendingTransactions, prefetchProducts } from '../lib/sync'
import { useSyncStore } from '../stores/syncStore'

export function useOfflineSync() {
  const isOnline = useNetworkStatus()
  const setSyncing = useSyncStore(s => s.setSyncing)
  const updatePendingCount = useSyncStore(s => s.updatePendingCount)
  const hasRunRef = useRef(false)

  useEffect(() => {
    updatePendingCount()
  }, [])

  useEffect(() => {
    if (!isOnline) return
    if (hasRunRef.current) return
    hasRunRef.current = true

    const run = async () => {
      setSyncing(true)
      try {
        await syncPendingTransactions()
        await prefetchProducts()
      } finally {
        setSyncing(false)
        await updatePendingCount()
        hasRunRef.current = false
      }
    }

    run()
  }, [isOnline])

  return { isOnline }
}
