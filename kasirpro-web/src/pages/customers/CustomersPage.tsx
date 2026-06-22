import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'

interface Customer {
  id: string
  name: string
  phone?: string
  email?: string
  points: number
  tier: string
}

const TIER_COLORS: Record<string, string> = {
  platinum: 'bg-purple-100 text-purple-700',
  gold: 'bg-yellow-100 text-yellow-700',
  silver: 'bg-gray-100 text-gray-600',
  bronze: 'bg-orange-100 text-orange-700',
}

export default function CustomersPage() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const qc = useQueryClient()

  const { data: customers = [] } = useQuery<Customer[]>({
    queryKey: ['customers', search],
    queryFn: () => api.get('/customers', { params: { search } }).then(r => r.data),
  })

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Pelanggan</h1>
        <button onClick={() => setShowForm(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
          + Tambah Pelanggan
        </button>
      </div>

      <input
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="Cari nama / no. HP..."
        className="border rounded-lg px-3 py-2 w-full mb-4 text-sm"
      />

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50 text-left text-gray-500">
              <th className="px-4 py-3">Nama</th>
              <th className="px-4 py-3">No. HP</th>
              <th className="px-4 py-3">Poin</th>
              <th className="px-4 py-3">Tier</th>
            </tr>
          </thead>
          <tbody>
            {customers.map(c => (
              <tr key={c.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{c.name}</td>
                <td className="px-4 py-3 text-gray-500">{c.phone || '—'}</td>
                <td className="px-4 py-3 font-mono">{c.points.toLocaleString('id-ID')}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${TIER_COLORS[c.tier] || ''}`}>
                    {c.tier}
                  </span>
                </td>
              </tr>
            ))}
            {customers.length === 0 && (
              <tr><td colSpan={4} className="text-center py-8 text-gray-400">Belum ada pelanggan</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showForm && (
        <CustomerForm
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); qc.invalidateQueries({ queryKey: ['customers'] }) }}
        />
      )}
    </div>
  )
}

function CustomerForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: '', phone: '', email: '' })
  const mut = useMutation({
    mutationFn: () => api.post('/customers', form),
    onSuccess: onSaved,
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl p-6 w-96" onClick={e => e.stopPropagation()}>
        <h2 className="font-bold mb-4">Tambah Pelanggan</h2>
        {[
          { key: 'name', placeholder: 'Nama lengkap' },
          { key: 'phone', placeholder: 'No. HP' },
          { key: 'email', placeholder: 'Email (opsional)' },
        ].map(({ key, placeholder }) => (
          <input
            key={key}
            placeholder={placeholder}
            value={form[key as keyof typeof form]}
            onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
            className="w-full border rounded px-3 py-2 mb-2 text-sm"
          />
        ))}
        <div className="flex gap-2 mt-2">
          <button onClick={onClose} className="flex-1 py-2 border rounded">Batal</button>
          <button onClick={() => mut.mutate()} className="flex-1 py-2 bg-blue-600 text-white rounded">Simpan</button>
        </div>
      </div>
    </div>
  )
}
