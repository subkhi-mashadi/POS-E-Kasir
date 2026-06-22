import { db } from './db'
import api from './api'

const MAX_RETRIES = 3
const BACKOFF_MS = [1000, 2000, 4000]

export async function syncPendingTransactions(): Promise<{ synced: number; failed: number }> {
  const pending = await db.transactions
    .where('sync_status')
    .equals('pending_sync')
    .toArray()

  let synced = 0
  let failed = 0

  for (const tx of pending) {
    if ((tx.retry_count ?? 0) >= MAX_RETRIES) {
      await db.transactions.update(tx.id!, { sync_status: 'failed' })
      failed++
      continue
    }

    const delay = BACKOFF_MS[tx.retry_count ?? 0] ?? 4000
    await sleep(delay)

    try {
      await api.post('/transactions', {
        branch_schema: 'public',
        local_id: tx.local_id,
        cashier_id: tx.cashier_id,
        customer_id: tx.customer_id,
        items: tx.items,
        subtotal: tx.subtotal,
        discount: tx.discount,
        tax: tx.tax,
        total: tx.total,
        payment_method: tx.payment_method,
        payment_detail: tx.payment_detail,
        created_at: tx.created_at,
      })
      await db.transactions.update(tx.id!, {
        sync_status: 'synced',
        synced_at: new Date().toISOString(),
      })
      synced++
    } catch (err: unknown) {
      const retryCount = (tx.retry_count ?? 0) + 1
      await db.transactions.update(tx.id!, {
        retry_count: retryCount,
        sync_status: retryCount >= MAX_RETRIES ? 'failed' : 'pending_sync',
      })
      failed++
    }
  }

  return { synced, failed }
}

export async function prefetchProducts(): Promise<void> {
  const newest = await db.products.orderBy('updated_at').last()
  const since = newest?.updated_at

  const params: Record<string, string> = {}
  if (since) params.since = since

  const res = await api.get('/products/sync', { params })
  if (res.data?.length) {
    await db.products.bulkPut(res.data)
  }
}

export async function getPendingCount(): Promise<number> {
  return db.transactions.where('sync_status').equals('pending_sync').count()
}

function sleep(ms: number) {
  return new Promise(r => setTimeout(r, ms))
}
