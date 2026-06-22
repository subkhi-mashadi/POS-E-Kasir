import type { CartItem } from '../../pages/pos/PosPage'

interface Props {
  items: CartItem[]
  subtotal: number
  tax: number
  total: number
  onUpdateQty: (product_id: string, qty: number) => void
  onClear: () => void
  onCheckout: () => void
}

export default function Cart({ items, subtotal, tax, total, onUpdateQty, onClear, onCheckout }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b flex items-center justify-between">
        <span className="font-semibold">Keranjang</span>
        {items.length > 0 && (
          <button onClick={onClear} className="text-red-400 text-xs hover:text-red-600">Kosongkan</button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {items.length === 0
          ? <div className="text-center text-gray-400 mt-20 text-sm">Tambah produk ke keranjang</div>
          : items.map(item => (
            <div key={item.product_id} className="flex items-center gap-2">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{item.name}</div>
                <div className="text-xs text-gray-500">Rp {item.unit_price.toLocaleString('id-ID')}</div>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => onUpdateQty(item.product_id, item.qty - 1)} className="w-6 h-6 rounded bg-gray-100 text-sm hover:bg-gray-200">−</button>
                <span className="w-8 text-center text-sm">{item.qty}</span>
                <button onClick={() => onUpdateQty(item.product_id, item.qty + 1)} className="w-6 h-6 rounded bg-gray-100 text-sm hover:bg-gray-200">+</button>
              </div>
              <div className="text-sm font-medium w-20 text-right">Rp {item.subtotal.toLocaleString('id-ID')}</div>
            </div>
          ))
        }
      </div>

      <div className="border-t p-3 space-y-1">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Subtotal</span><span>Rp {subtotal.toLocaleString('id-ID')}</span>
        </div>
        <div className="flex justify-between text-sm text-gray-600">
          <span>PPN 11%</span><span>Rp {tax.toLocaleString('id-ID')}</span>
        </div>
        <div className="flex justify-between font-bold text-lg border-t pt-2">
          <span>Total</span><span className="text-blue-600">Rp {total.toLocaleString('id-ID')}</span>
        </div>
        <button
          onClick={onCheckout}
          disabled={items.length === 0}
          className="w-full mt-2 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Bayar
        </button>
      </div>
    </div>
  )
}
