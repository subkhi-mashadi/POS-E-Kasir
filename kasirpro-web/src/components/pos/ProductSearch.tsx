import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'
import { db } from '../../lib/db'
import { useNetworkStatus } from '../../hooks/useNetworkStatus'
import type { LocalProduct } from '../../lib/db'

interface Props {
  onAddToCart: (product: LocalProduct) => void
}

export default function ProductSearch({ onAddToCart }: Props) {
  const [search, setSearch] = useState('')
  const isOnline = useNetworkStatus()

  const { data: products = [] } = useQuery({
    queryKey: ['products', search],
    queryFn: async () => {
      if (isOnline) {
        const res = await api.get('/products', { params: { search, per_page: 50 } })
        const items = res.data.items as LocalProduct[]
        await db.products.bulkPut(items)
        return items
      }
      if (search) {
        return db.products.where('name').startsWithIgnoreCase(search).toArray()
      }
      return db.products.toArray()
    },
    staleTime: 60_000,
  })

  return (
    <div>
      <input
        type="text"
        placeholder="Cari produk / barcode..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="w-full border rounded-lg px-4 py-2 mb-4 text-sm"
        autoFocus
      />
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {products.map(p => (
          <button
            key={p.id}
            onClick={() => onAddToCart(p)}
            className="bg-white rounded-lg border p-3 text-left hover:border-blue-400 hover:shadow transition-all"
          >
            {p.image_url
              ? <img src={p.image_url} alt={p.name} className="w-full h-24 object-cover rounded mb-2" />
              : <div className="w-full h-24 bg-gray-100 rounded mb-2 flex items-center justify-center text-gray-400 text-2xl">📦</div>
            }
            <div className="text-sm font-medium truncate">{p.name}</div>
            <div className="text-blue-600 font-bold text-sm">Rp {p.base_price.toLocaleString('id-ID')}</div>
          </button>
        ))}
        {products.length === 0 && (
          <div className="col-span-full text-center text-gray-400 py-10">Tidak ada produk ditemukan</div>
        )}
      </div>
    </div>
  )
}
