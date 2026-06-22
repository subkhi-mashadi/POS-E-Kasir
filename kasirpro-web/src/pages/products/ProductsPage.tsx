import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../lib/api'

interface Product {
  id: string
  sku: string
  name: string
  base_price: number
  barcode?: string
  is_active: boolean
}

export default function ProductsPage() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['products-admin', search],
    queryFn: () => api.get('/products', { params: { search, per_page: 100 } }).then(r => r.data),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/products/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['products-admin'] }),
  })

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Produk</h1>
        <button onClick={() => setShowForm(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">+ Tambah Produk</button>
      </div>
      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Cari..." className="border rounded-lg px-3 py-2 w-full mb-4 text-sm" />
      <table className="w-full text-sm">
        <thead><tr className="border-b text-left text-gray-500">
          <th className="pb-2">SKU</th><th>Nama</th><th>Harga</th><th>Barcode</th><th>Status</th><th></th>
        </tr></thead>
        <tbody>
          {data?.items?.map((p: Product) => (
            <tr key={p.id} className="border-b hover:bg-gray-50">
              <td className="py-2 font-mono text-xs">{p.sku}</td>
              <td>{p.name}</td>
              <td>Rp {p.base_price.toLocaleString('id-ID')}</td>
              <td className="text-xs text-gray-500">{p.barcode || '—'}</td>
              <td><span className={`px-2 py-0.5 rounded text-xs ${p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{p.is_active ? 'Aktif' : 'Nonaktif'}</span></td>
              <td><button onClick={() => deleteMut.mutate(p.id)} className="text-red-400 hover:text-red-600 text-xs">Hapus</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      {showForm && <ProductForm onClose={() => setShowForm(false)} onSaved={() => { setShowForm(false); qc.invalidateQueries({ queryKey: ['products-admin'] }) }} />}
    </div>
  )
}

function ProductForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ sku: '', name: '', base_price: '', barcode: '' })
  const mut = useMutation({
    mutationFn: () => api.post('/products', { ...form, base_price: Number(form.base_price) }),
    onSuccess: onSaved,
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-xl p-6 w-96" onClick={e => e.stopPropagation()}>
        <h2 className="font-bold mb-4">Tambah Produk</h2>
        {(['sku', 'name', 'base_price', 'barcode'] as const).map(f => (
          <input key={f} placeholder={f} value={form[f]} onChange={e => setForm(p => ({ ...p, [f]: e.target.value }))} className="w-full border rounded px-3 py-2 mb-2 text-sm" />
        ))}
        <div className="flex gap-2 mt-2">
          <button onClick={onClose} className="flex-1 py-2 border rounded">Batal</button>
          <button onClick={() => mut.mutate()} className="flex-1 py-2 bg-blue-600 text-white rounded">Simpan</button>
        </div>
      </div>
    </div>
  )
}
