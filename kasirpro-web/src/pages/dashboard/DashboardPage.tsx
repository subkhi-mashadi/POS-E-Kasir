import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'

interface BranchStats {
  branch_id: string
  branch_name: string
  today_sales: number
  today_transactions: number
}

interface ConsolidatedData {
  branches: BranchStats[]
  total_today_sales: number
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery<ConsolidatedData>({
    queryKey: ['consolidated-dashboard'],
    queryFn: () => api.get('/branches/consolidated').then(r => r.data),
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Memuat dashboard...</div>
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard Pusat</h1>
        <span className="text-sm text-gray-400">Auto-refresh 30 detik</span>
      </div>

      {/* Total banner */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-6 text-white mb-6">
        <div className="text-sm opacity-80">Total Penjualan Hari Ini — Semua Cabang</div>
        <div className="text-4xl font-bold mt-1">
          Rp {(data?.total_today_sales ?? 0).toLocaleString('id-ID')}
        </div>
        <div className="text-sm opacity-70 mt-1">{data?.branches.length ?? 0} cabang aktif</div>
      </div>

      {/* Per-branch grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.branches.map(branch => (
          <div key={branch.branch_id} className="bg-white rounded-xl border p-5 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="font-semibold">{branch.branch_name}</div>
                <div className="text-xs text-gray-400 font-mono">{branch.branch_id.slice(0, 8)}</div>
              </div>
              <a
                href={`/branches/${branch.branch_id}`}
                className="text-xs text-blue-500 hover:text-blue-700"
              >
                Detail →
              </a>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Penjualan hari ini</span>
                <span className="font-semibold text-green-600">
                  Rp {branch.today_sales.toLocaleString('id-ID')}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Transaksi</span>
                <span className="font-semibold">{branch.today_transactions}</span>
              </div>
            </div>
            <div className="mt-3 bg-gray-100 rounded-full h-1.5">
              <div
                className="bg-blue-500 h-1.5 rounded-full"
                style={{
                  width: data.total_today_sales > 0
                    ? `${Math.min(100, (branch.today_sales / data.total_today_sales) * 100)}%`
                    : '0%'
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Cabang Baru', href: '/branches/new', icon: '🏪' },
          { label: 'Sync Produk', href: '/branches/sync', icon: '🔄' },
          { label: 'Transfer Stok', href: '/stock/transfer', icon: '📦' },
          { label: 'Promosi', href: '/promotions', icon: '🎁' },
        ].map(({ label, href, icon }) => (
          <a
            key={label}
            href={href}
            className="bg-white border rounded-xl p-4 flex flex-col items-center gap-2 hover:border-blue-400 hover:shadow transition-all text-center"
          >
            <span className="text-2xl">{icon}</span>
            <span className="text-sm font-medium">{label}</span>
          </a>
        ))}
      </div>
    </div>
  )
}
