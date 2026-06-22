import Dexie, { Table } from 'dexie'

export interface LocalTransaction {
  id?: number
  local_id: string
  invoice_no: string
  cashier_id: string
  customer_id?: string
  items: LocalTransactionItem[]
  subtotal: number
  discount: number
  tax: number
  total: number
  payment_method: string
  payment_detail: Record<string, unknown>
  sync_status: 'pending_sync' | 'synced' | 'failed'
  retry_count: number
  created_at: string
  synced_at?: string
}

export interface LocalTransactionItem {
  product_id: string
  variant_id?: string
  qty: number
  unit_price: number
  discount: number
  subtotal: number
}

export interface LocalProduct {
  id: string
  sku: string
  name: string
  category_id: string
  base_price: number
  barcode?: string
  image_url?: string
  is_active: boolean
  updated_at: string
}

export interface LocalCustomer {
  id: string
  name: string
  phone?: string
  email?: string
  points: number
  tier: string
}

export interface SyncQueue {
  id?: number
  type: 'transaction' | 'stock_adjust'
  payload: Record<string, unknown>
  retry_count: number
  created_at: string
  last_error?: string
}

class KasirProDB extends Dexie {
  transactions!: Table<LocalTransaction>
  products!: Table<LocalProduct>
  customers!: Table<LocalCustomer>
  syncQueue!: Table<SyncQueue>

  constructor() {
    super('KasirProDB')
    this.version(2).stores({
      transactions: '++id, local_id, sync_status, created_at, cashier_id',
      products: 'id, sku, barcode, category_id, name, is_active',
      customers: 'id, phone, name',
      syncQueue: '++id, type, retry_count, created_at',
    })
  }
}

export const db = new KasirProDB()
