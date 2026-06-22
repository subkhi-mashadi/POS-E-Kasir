import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'

interface Promotion {
  id: string
  name: string
  type: string
  discount_value: number
  start_at: string
  end_at: string
}

export default function PromotionsPage() {
  const [showForm, setShowForm] = useState(false)
  const qc = useQueryClient()

  const { data: promotions = [] } = useQuery<Promotion[]>({
    queryKey: ['promotions'],
    queryFn: () => api.get('/promotions', { params: { active_only: false } }).then(r => r.data),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/promotions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['promotions'] }),
  })

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Promosi & Diskon</h1>
        <button onClick={() => setShowForm(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
          + Tambah Promosi
        </button>
      </div>

      <div className="space-y-3">
        {promotions.map(p => (
          <div key={p.id} className="bg-white border rounded-xl p-4 flex items-center gap-4">
            <div className="flex-1">
              <div className="font-semibold">{p.name}</div>
              <div className="text-xs text-gray-500 mt-0.5">
                {p.type === 'percentage' ? `${p.discount_value}% diskon` :
                 p.type === 'fixed' ? `Rp ${Number(p.discount_value).toLocaleString('id-ID')} diskon` :
                 'Buy X Get Y'}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">
                {new Date(p.start_at).toLocaleDateString('id-ID')} — {new Date(p.end_at).toLocaleDateString('id-ID')}
              </div>
            </div>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
              new Date(p.end_at) >= new Date() ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
            }`}>
              {new Date(p.end_at) >= new Date() ? 'Aktif' : 'Berakhir'}
            </span>
            <button onClick={() => deleteMut.mutate(p.id)} className="text-red-400 hover:text-red-600 text-sm">Hapus</button>
          </div>
        ))}
        {promotions.length === 0 && (
          <div className="text-center py-12 text-gray-400">Belum ada promosi</div>
        )}
      </div>

      {showForm && (
        <PromotionForm
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); qc.invalidateQueries({ queryKey: ['promotions'] }) }}
        />
      )}
    </div>
  )
}

function PromotionForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({
    name: '', type: 'percentage', discount_value: '',
    start_at: '', end_at: '', conditions: '{}'
  })
  const mut = useMutation({
    mutationFn: () => api.post('/promotions', {
      ...form,
      discount_value: Number(form.discount_value),
      conditions: JSON.parse(form.conditions || '{}'),
    }),
    onSuccess: onSaved,
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl p-6 w-[420px]" onClick={e => e.stopPropagation()}>
        <h2 className="font-bold mb-4">Tambah Promosi</h2>
        <input placeholder="Nama promosi" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="w-full border rounded px-3 py-2 mb-2 text-sm" />
        <select value={form.type} onChange={e => setForm(p => ({ ...p, type: e.target.value }))} className="w-full border rounded px-3 py-2 mb-2 text-sm">
          <option value="percentage">Persentase (%)</option>
          <option value="fixed">Nominal (Rp)</option>
          <option value="buy_x_get_y">Buy X Get Y</option>
        </select>
        <input type="number" placeholder="Nilai diskon" value={form.discount_value} onChange={e => setForm(p => ({ ...p, discount_value: e.target.value }))} className="w-full border rounded px-3 py-2 mb-2 text-sm" />
        <div className="flex gap-2 mb-2">
          <input type="datetime-local" value={form.start_at} onChange={e => setForm(p => ({ ...p, start_at: e.target.value }))} className="flex-1 border rounded px-3 py-2 text-sm" />
          <input type="datetime-local" value={form.end_at} onChange={e => setForm(p => ({ ...p, end_at: e.target.value }))} className="flex-1 border rounded px-3 py-2 text-sm" />
        </div>
        <textarea placeholder='Kondisi JSON (opsional): {"min_purchase": 100000}' value={form.conditions} onChange={e => setForm(p => ({ ...p, conditions: e.target.value }))} className="w-full border rounded px-3 py-2 mb-3 text-sm h-16 resize-none font-mono text-xs" />
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2 border rounded">Batal</button>
          <button onClick={() => mut.mutate()} className="flex-1 py-2 bg-blue-600 text-white rounded">Simpan</button>
        </div>
      </div>
    </div>
  )
}
