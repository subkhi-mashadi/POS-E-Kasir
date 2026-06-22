import { create } from 'zustand'
import { getPendingCount } from '../lib/sync'

interface SyncState {
  isSyncing: boolean
  pendingCount: number
  setSyncing: (v: boolean) => void
  setPendingCount: (n: number) => void
  updatePendingCount: () => Promise<void>
}

export const useSyncStore = create<SyncState>((set) => ({
  isSyncing: false,
  pendingCount: 0,
  setSyncing: (isSyncing) => set({ isSyncing }),
  setPendingCount: (pendingCount) => set({ pendingCount }),
  updatePendingCount: async () => {
    const count = await getPendingCount()
    set({ pendingCount: count })
  },
}))
