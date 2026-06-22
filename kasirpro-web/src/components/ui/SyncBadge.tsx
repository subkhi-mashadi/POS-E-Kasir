import { useSyncStore } from '../../stores/syncStore'
import { useNetworkStatus } from '../../hooks/useNetworkStatus'

export default function SyncBadge() {
  const isOnline = useNetworkStatus()
  const { isSyncing, pendingCount } = useSyncStore()

  if (isSyncing) {
    return (
      <div className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 animate-pulse">
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-spin" style={{ animationDuration: '1s' }} />
        Menyinkronkan...
      </div>
    )
  }

  if (!isOnline && pendingCount > 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full bg-orange-100 text-orange-700">
        <span className="w-2 h-2 rounded-full bg-orange-500" />
        Offline · {pendingCount} transaksi tertunda
      </div>
    )
  }

  if (!isOnline) {
    return (
      <div className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">
        <span className="w-2 h-2 rounded-full bg-gray-400" />
        Offline
      </div>
    )
  }

  if (pendingCount > 0) {
    return (
      <div className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-700">
        <span className="w-2 h-2 rounded-full bg-yellow-500" />
        {pendingCount} belum tersinkron
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
      <span className="w-2 h-2 rounded-full bg-green-500" />
      Online
    </div>
  )
}
