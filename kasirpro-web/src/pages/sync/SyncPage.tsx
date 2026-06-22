import { useState, useEffect } from 'react'
import { db } from '../../lib/db'
import { syncPendingTransactions } from '../../lib/sync'
import { useSyncStore } from '../../stores/syncStore'
import { useNetworkStatus } from '../../hooks/useNetworkStatus'
import type { LocalTransaction } from '../../lib/db'

export default function SyncPage() {
  const [txList, setTxList] = useState<LocalTransaction[]>([])
  const isOnline = useNetworkStatus()
  const { isSyncing, setSyncing, updatePendingCount } = useSyncStore()

  useEffect(() => {
    loadTx()
  }, [])

  async function loadTx() {
    const all = await db.transactions.orderBy('created_at').reverse().limit(50).toArray()
    setTxList(all)
  }

  async function handleManualSync() {
    if (!isOnline) return
    setSyncing(true)
    await syncPendingTransactions()
    setSyncing(false)
    await updatePendingCount()
    await loadTx()
  }

  const pending = txList.filter(t => t.sync_status === 'pending_sync').length
  const failed = txList.filter(t => t.sync_status === 'failed').length
  const synced = txList.filter(t => t.sync_status === 'synced').length

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Status Sinkronisasi</h1>
        <button
          onClick={handleManualSync}
          disabled={!isOnline || isSyncing}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-40"
        >
          {isSyncing ? 'Menyinkronkan...' : 'Sync Sekarang'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Tertunda', value: pending, color: 'orange' },
          { label: 'Gagal', value: failed, color: 'red' },
          { label: 'Tersinkron', value: synced, color: 'green' },
        ].map(({ label, value, color }) => (
          <div key={label} className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4 text-center`}>
            <div className={`text-3xl font-bold text-${color}-600`}>{value}</div>
            <div className={`text-sm text-${color}-700`}>{label}</div>
          </div>
        ))}
      </div>

      {/* Transaction list */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50 text-left text-gray-500">
              <th className="px-4 py-3">Invoice</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Waktu</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Retry</th>
            </tr>
          </thead>
          <tbody>
            {txList.map(tx => (
              <tr key={tx.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2 font-mono text-xs">{tx.invoice_no}</td>
                <td className="px-4 py-2">Rp {tx.total.toLocaleString('id-ID')}</td>
                <td className="px-4 py-2 text-gray-500 text-xs">{new Date(tx.created_at).toLocaleString('id-ID')}</td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    tx.sync_status === 'synced' ? 'bg-green-100 text-green-700' :
                    tx.sync_status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-orange-100 text-orange-700'
                  }`}>
                    {tx.sync_status === 'synced' ? 'Tersinkron' :
                     tx.sync_status === 'failed' ? 'Gagal' : 'Tertunda'}
                  </span>
                </td>
                <td className="px-4 py-2 text-xs text-gray-400">{tx.retry_count ?? 0}×</td>
              </tr>
            ))}
            {txList.length === 0 && (
              <tr><td colSpan={5} className="text-center py-8 text-gray-400">Belum ada transaksi</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
