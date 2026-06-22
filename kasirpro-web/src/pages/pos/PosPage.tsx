import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { v4 as uuidv4 } from 'uuid'
import api from '../../lib/api'
import { db } from '../../lib/db'
import { useNetworkStatus } from '../../hooks/useNetworkStatus'
import { useAuthStore } from '../../stores/authStore'
import { useSyncStore } from '../../stores/syncStore'
import SyncBadge from '../../components/ui/SyncBadge'
import ProductSearch from '../../components/pos/ProductSearch'
import Cart from '../../components/pos/Cart'
import PaymentModal from '../../components/pos/PaymentModal'
import type { LocalProduct } from '../../lib/db'

export interface CartItem {
  product_id: string
  name: string
  qty: number
  unit_price: number
  discount: number
  subtotal: number
}

export default function PosPage() {
  const isOnline = useNetworkStatus()
  const user = useAuthStore(s => s.user)
  const updatePendingCount = useSyncStore(s => s.updatePendingCount)
  const [cart, setCart] = useState<CartItem[]>([])
  const [showPayment, setShowPayment] = useState(false)
  const [lastInvoice, setLastInvoice] = useState<string | null>(null)
  const [lastTxId, setLastTxId] = useState<string | undefined>(undefined)

  const subtotal = cart.reduce((s, i) => s + i.subtotal, 0)
  const tax = Math.round(subtotal * 0.11)
  const total = subtotal + tax

  function addToCart(product: LocalProduct) {
    setCart(prev => {
      const existing = prev.find(i => i.product_id === product.id)
      if (existing) {
        return prev.map(i =>
          i.product_id === product.id
            ? { ...i, qty: i.qty + 1, subtotal: (i.qty + 1) * i.unit_price }
            : i
        )
      }
      return [...prev, {
        product_id: product.id,
        name: product.name,
        qty: 1,
        unit_price: product.base_price,
        discount: 0,
        subtotal: product.base_price,
      }]
    })
  }

  function updateQty(product_id: string, qty: number) {
    if (qty <= 0) {
      setCart(prev => prev.filter(i => i.product_id !== product_id))
      return
    }
    setCart(prev =>
      prev.map(i =>
        i.product_id === product_id
          ? { ...i, qty, subtotal: qty * i.unit_price - i.discount }
          : i
      )
    )
  }

  function clearCart() {
    setCart([])
    setShowPayment(false)
  }

  async function processTransaction(paymentMethod: string, paymentDetail: Record<string, unknown>) {
    const local_id = uuidv4()
    const txData = {
      branch_schema: 'public',
      local_id,
      cashier_id: user?.id || '',
      items: cart.map(i => ({
        product_id: i.product_id,
        qty: i.qty,
        unit_price: i.unit_price,
        discount: i.discount,
        subtotal: i.subtotal,
      })),
      subtotal,
      discount: 0,
      tax,
      total,
      payment_method: paymentMethod,
      payment_detail: paymentDetail,
      created_at: new Date().toISOString(),
    }

    if (isOnline) {
      try {
        const res = await api.post('/transactions', txData)
        setLastInvoice(res.data.invoice_no)
        setLastTxId(res.data.id)
        clearCart()
        return
      } catch {
        // fall through to offline save
      }
    }

    const localInvoice = `LOCAL-${local_id.slice(0, 8).toUpperCase()}`
    await db.transactions.add({
      local_id,
      invoice_no: localInvoice,
      cashier_id: txData.cashier_id,
      items: txData.items,
      subtotal: txData.subtotal,
      discount: txData.discount,
      tax: txData.tax,
      total: txData.total,
      payment_method: paymentMethod,
      payment_detail: paymentDetail,
      sync_status: 'pending_sync',
      retry_count: 0,
      created_at: txData.created_at,
    })
    await updatePendingCount()
    setLastInvoice(localInvoice)
    setLastTxId(undefined) // offline — tidak ada server ID
    clearCart()
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-10 bg-white border-b px-4 py-2 flex items-center gap-3 shadow-sm">
        <span className="text-lg font-bold text-blue-600">KasirPro</span>
        <span className="text-sm text-gray-500">{user?.name}</span>
        <a href="/dashboard" className="text-sm text-gray-400 hover:text-gray-700 ml-2">Dashboard</a>
        <a href="/products" className="text-sm text-gray-400 hover:text-gray-700">Produk</a>
        <a href="/sync" className="text-sm text-gray-400 hover:text-gray-700">Sync</a>
        <div className="ml-auto">
          <SyncBadge />
        </div>
      </div>

      <div className="flex w-full pt-12">
        {/* Left: Product search */}
        <div className="flex-1 p-4 overflow-y-auto">
          <ProductSearch onAddToCart={addToCart} />
        </div>

        {/* Right: Cart */}
        <div className="w-96 bg-white border-l flex flex-col">
          <Cart
            items={cart}
            subtotal={subtotal}
            tax={tax}
            total={total}
            onUpdateQty={updateQty}
            onClear={clearCart}
            onCheckout={() => setShowPayment(true)}
          />
        </div>
      </div>

      {showPayment && (
        <PaymentModal
          total={total}
          transactionId={lastTxId}
          branchSchema="public"
          cashierName={user?.name || 'Kasir'}
          branchName="KasirPro"
          onClose={() => setShowPayment(false)}
          onConfirm={processTransaction}
        />
      )}

      {lastInvoice && (
        <div className="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <span>✓ {lastInvoice}</span>
          <button onClick={() => { setLastInvoice(null); setLastTxId(undefined) }} className="text-green-200 hover:text-white">
            ✕
          </button>
        </div>
      )}
    </div>
  )
}
