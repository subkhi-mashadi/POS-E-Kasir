import { useState } from 'react'
import api from '../../lib/api'

interface Props {
  total: number
  transactionId?: string
  branchSchema?: string
  cashierName?: string
  branchName?: string
  onClose: () => void
  onConfirm: (method: string, detail: Record<string, unknown>) => Promise<void>
}

const METHODS = [
  { id: 'cash', label: 'Tunai' },
  { id: 'qris', label: 'QRIS' },
  { id: 'transfer', label: 'Transfer' },
  { id: 'debit', label: 'Debit' },
  { id: 'credit', label: 'Kredit' },
]

export default function PaymentModal({
  total, transactionId, branchSchema = 'public',
  cashierName = 'Kasir', branchName = 'KasirPro',
  onClose, onConfirm,
}: Props) {
  const [method, setMethod] = useState('cash')
  const [cashGiven, setCashGiven] = useState('')
  const [phone, setPhone] = useState('')
  const [sendWA, setSendWA] = useState(false)
  const [loading, setLoading] = useState(false)
  const [sendingWA, setSendingWA] = useState(false)
  const [waResult, setWaResult] = useState<'ok' | 'error' | null>(null)

  const change = method === 'cash' ? Math.max(0, Number(cashGiven) - total) : 0
  const canConfirm = method !== 'cash' || Number(cashGiven) >= total

  async function handleConfirm() {
    setLoading(true)
    await onConfirm(method, method === 'cash' ? { cash_given: Number(cashGiven), change } : {})
    setLoading(false)
  }

  async function handleSendWA() {
    if (!transactionId || !phone) return
    setSendingWA(true)
    try {
      await api.post(`/transactions/${transactionId}/receipt/send-whatsapp`, null, {
        params: {
          phone: phone.replace(/^0/, '62').replace(/[^0-9]/g, ''),
          branch_schema: branchSchema,
          cashier_name: cashierName,
          branch_name: branchName,
        },
      })
      setWaResult('ok')
    } catch {
      setWaResult('error')
    } finally {
      setSendingWA(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl p-6 w-96 shadow-xl" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-bold mb-4">Pembayaran</h2>

        <div className="text-center mb-4">
          <div className="text-sm text-gray-500">Total Tagihan</div>
          <div className="text-3xl font-bold text-blue-600">Rp {total.toLocaleString('id-ID')}</div>
        </div>

        {/* Payment method */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {METHODS.map(m => (
            <button
              key={m.id}
              onClick={() => setMethod(m.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                method === m.id ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {method === 'cash' && (
          <div className="mb-4">
            <label className="text-sm text-gray-600 mb-1 block">Uang Diterima</label>
            <input
              type="number"
              value={cashGiven}
              onChange={e => setCashGiven(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-lg font-mono"
              placeholder="0"
              autoFocus
            />
            {cashGiven && (
              <div className="mt-2 flex justify-between text-sm">
                <span className="text-gray-500">Kembalian</span>
                <span className={`font-bold ${change >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                  Rp {change.toLocaleString('id-ID')}
                </span>
              </div>
            )}
            <div className="flex gap-2 mt-2 flex-wrap">
              {[50000, 100000, 150000, 200000].map(v => (
                <button
                  key={v}
                  onClick={() => setCashGiven(String(v))}
                  className="px-2 py-1 text-xs bg-gray-100 rounded hover:bg-gray-200"
                >
                  {v / 1000}rb
                </button>
              ))}
              <button
                onClick={() => setCashGiven(String(Math.ceil(total / 1000) * 1000))}
                className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                Pas
              </button>
            </div>
          </div>
        )}

        {/* WhatsApp struk */}
        <div className="mb-4 border-t pt-3">
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input
              type="checkbox"
              checked={sendWA}
              onChange={e => setSendWA(e.target.checked)}
              className="rounded"
            />
            Kirim struk via WhatsApp
          </label>
          {sendWA && (
            <div className="mt-2 flex gap-2">
              <input
                type="tel"
                placeholder="08xxxxxxxxxx"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                className="flex-1 border rounded px-3 py-1.5 text-sm"
              />
              {transactionId && (
                <button
                  onClick={handleSendWA}
                  disabled={!phone || sendingWA}
                  className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-40 whitespace-nowrap"
                >
                  {sendingWA ? '...' : '📱 Kirim'}
                </button>
              )}
            </div>
          )}
          {waResult === 'ok' && (
            <p className="text-green-600 text-xs mt-1">✓ Struk berhasil dikirim ke WhatsApp</p>
          )}
          {waResult === 'error' && (
            <p className="text-red-500 text-xs mt-1">✗ Gagal kirim. Cek nomor HP atau konfigurasi Fonnte.</p>
          )}
        </div>

        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2 border rounded-lg hover:bg-gray-50">
            Batal
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canConfirm || loading}
            className="flex-1 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-40"
          >
            {loading ? 'Memproses...' : 'Konfirmasi'}
          </button>
        </div>
      </div>
    </div>
  )
}
