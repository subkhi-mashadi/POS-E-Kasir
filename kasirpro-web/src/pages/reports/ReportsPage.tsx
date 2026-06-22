import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'

type ReportTab = 'sales' | 'products' | 'cashier' | 'stock'

interface SalesRow {
  period: string
  transaction_count: number
  total_sales: number
  avg_transaction: number
}

interface ProductRow {
  product_name: string
  sku: string
  total_qty_sold: number
  total_revenue: number
}

interface CashierRow {
  cashier_name: string
  transaction_count: number
  total_sales: number
}

interface StockRow {
  product_name: string
  sku: string
  current_qty: number
  min_qty: number
  stock_value: number
  is_low: boolean
}

export default function ReportsPage() {
  const [tab, setTab] = useState<ReportTab>('sales')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [groupBy, setGroupBy] = useState<'day' | 'week' | 'month'>('day')
  const [exporting, setExporting] = useState(false)

  const branchSchema = 'public'

  const { data: salesData = [], isLoading: salesLoading } = useQuery<SalesRow[]>({
    queryKey: ['report-sales', branchSchema, dateFrom, dateTo, groupBy],
    queryFn: () => api.get('/reports/sales', { params: { branch_schema: branchSchema, date_from: dateFrom || undefined, date_to: dateTo || undefined, group_by: groupBy } }).then(r => r.data),
    enabled: tab === 'sales',
  })

  const { data: productsData = [] } = useQuery<ProductRow[]>({
    queryKey: ['report-products', branchSchema, dateFrom, dateTo],
    queryFn: () => api.get('/reports/products', { params: { branch_schema: branchSchema, date_from: dateFrom || undefined, date_to: dateTo || undefined } }).then(r => r.data),
    enabled: tab === 'products',
  })

  const { data: cashierData = [] } = useQuery<CashierRow[]>({
    queryKey: ['report-cashier', branchSchema, dateFrom, dateTo],
    queryFn: () => api.get('/reports/cashier', { params: { branch_schema: branchSchema, date_from: dateFrom || undefined, date_to: dateTo || undefined } }).then(r => r.data),
    enabled: tab === 'cashier',
  })

  const { data: stockData = [] } = useQuery<StockRow[]>({
    queryKey: ['report-stock', branchSchema],
    queryFn: () => api.get('/reports/stock', { params: { branch_schema: branchSchema } }).then(r => r.data),
    enabled: tab === 'stock',
  })

  async function handleExport() {
    setExporting(true)
    try {
      const res = await api.get('/reports/export', {
        params: { report_type: tab, format: 'csv', branch_schema: branchSchema, date_from: dateFrom || undefined, date_to: dateTo || undefined }
      })
      alert(`Laporan sedang dibuat. Task ID: ${res.data.task_id}`)
    } finally {
      setExporting(false)
    }
  }

  const TABS: { id: ReportTab; label: string }[] = [
    { id: 'sales', label: 'Penjualan' },
    { id: 'products', label: 'Produk' },
    { id: 'cashier', label: 'Kasir' },
    { id: 'stock', label: 'Stok' },
  ]

  const totalSales = salesData.reduce((s, r) => s + r.total_sales, 0)
  const totalTx = salesData.reduce((s, r) => s + r.transaction_count, 0)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Laporan & Analitik</h1>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-40"
        >
          {exporting ? 'Mengekspor...' : '↓ Export CSV'}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <input
          type="date"
          value={dateFrom}
          onChange={e => setDateFrom(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm"
        />
        <input
          type="date"
          value={dateTo}
          onChange={e => setDateTo(e.target.value)}
          className="border rounded px-3 py-1.5 text-sm"
        />
        {tab === 'sales' && (
          <select value={groupBy} onChange={e => setGroupBy(e.target.value as typeof groupBy)} className="border rounded px-3 py-1.5 text-sm">
            <option value="day">Per Hari</option>
            <option value="week">Per Minggu</option>
            <option value="month">Per Bulan</option>
          </select>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Summary cards — sales tab only */}
      {tab === 'sales' && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Total Penjualan', value: `Rp ${totalSales.toLocaleString('id-ID')}`, color: 'blue' },
            { label: 'Total Transaksi', value: totalTx.toLocaleString('id-ID'), color: 'green' },
            { label: 'Rata-rata Transaksi', value: totalTx > 0 ? `Rp ${Math.round(totalSales / totalTx).toLocaleString('id-ID')}` : '—', color: 'purple' },
          ].map(({ label, value, color }) => (
            <div key={label} className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4`}>
              <div className={`text-sm text-${color}-600`}>{label}</div>
              <div className={`text-2xl font-bold text-${color}-700 mt-1`}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        {tab === 'sales' && (
          <table className="w-full text-sm">
            <thead><tr className="bg-gray-50 border-b text-left text-gray-500">
              <th className="px-4 py-3">Periode</th>
              <th className="px-4 py-3 text-right">Transaksi</th>
              <th className="px-4 py-3 text-right">Total Penjualan</th>
              <th className="px-4 py-3 text-right">Rata-rata</th>
            </tr></thead>
            <tbody>
              {salesData.map((r, i) => (
                <tr key={i} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3">{new Date(r.period).toLocaleDateString('id-ID', { dateStyle: 'medium' })}</td>
                  <td className="px-4 py-3 text-right">{r.transaction_count}</td>
                  <td className="px-4 py-3 text-right font-medium">Rp {r.total_sales.toLocaleString('id-ID')}</td>
                  <td className="px-4 py-3 text-right text-gray-500">Rp {Math.round(r.avg_transaction).toLocaleString('id-ID')}</td>
                </tr>
              ))}
              {salesLoading && <tr><td colSpan={4} className="text-center py-8 text-gray-400">Memuat...</td></tr>}
            </tbody>
          </table>
        )}

        {tab === 'products' && (
          <table className="w-full text-sm">
            <thead><tr className="bg-gray-50 border-b text-left text-gray-500">
              <th className="px-4 py-3">Produk</th>
              <th className="px-4 py-3">SKU</th>
              <th className="px-4 py-3 text-right">Qty Terjual</th>
              <th className="px-4 py-3 text-right">Revenue</th>
            </tr></thead>
            <tbody>
              {productsData.map((r, i) => (
                <tr key={i} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{r.product_name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.sku}</td>
                  <td className="px-4 py-3 text-right">{r.total_qty_sold}</td>
                  <td className="px-4 py-3 text-right">Rp {r.total_revenue.toLocaleString('id-ID')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === 'cashier' && (
          <table className="w-full text-sm">
            <thead><tr className="bg-gray-50 border-b text-left text-gray-500">
              <th className="px-4 py-3">Kasir</th>
              <th className="px-4 py-3 text-right">Transaksi</th>
              <th className="px-4 py-3 text-right">Total Penjualan</th>
            </tr></thead>
            <tbody>
              {cashierData.map((r, i) => (
                <tr key={i} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{r.cashier_name || '(unknown)'}</td>
                  <td className="px-4 py-3 text-right">{r.transaction_count}</td>
                  <td className="px-4 py-3 text-right font-medium text-green-600">Rp {r.total_sales.toLocaleString('id-ID')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {tab === 'stock' && (
          <table className="w-full text-sm">
            <thead><tr className="bg-gray-50 border-b text-left text-gray-500">
              <th className="px-4 py-3">Produk</th>
              <th className="px-4 py-3">SKU</th>
              <th className="px-4 py-3 text-right">Stok</th>
              <th className="px-4 py-3 text-right">Min</th>
              <th className="px-4 py-3 text-right">Nilai Stok</th>
              <th className="px-4 py-3">Status</th>
            </tr></thead>
            <tbody>
              {stockData.map((r, i) => (
                <tr key={i} className={`border-b hover:bg-gray-50 ${r.is_low ? 'bg-red-50' : ''}`}>
                  <td className="px-4 py-3 font-medium">{r.product_name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.sku}</td>
                  <td className="px-4 py-3 text-right font-bold">{r.current_qty}</td>
                  <td className="px-4 py-3 text-right text-gray-500">{r.min_qty}</td>
                  <td className="px-4 py-3 text-right">Rp {(r.stock_value || 0).toLocaleString('id-ID')}</td>
                  <td className="px-4 py-3">
                    {r.is_low
                      ? <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-700 font-medium">Menipis</span>
                      : <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-700">Aman</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
