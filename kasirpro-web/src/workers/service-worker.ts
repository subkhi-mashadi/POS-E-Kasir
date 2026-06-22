import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { StaleWhileRevalidate, NetworkFirst, CacheFirst } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { BackgroundSyncPlugin } from 'workbox-background-sync'

declare let self: ServiceWorkerGlobalScope

cleanupOutdatedCaches()
precacheAndRoute(self.__WB_MANIFEST)

// Products — stale while revalidate, 1 jam
registerRoute(
  ({ url }) => url.pathname.includes('/api/v1/products'),
  new StaleWhileRevalidate({
    cacheName: 'products-cache',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 3600, maxEntries: 500 }),
    ],
  })
)

// Gambar produk — cache first, 7 hari
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-cache',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 7 * 24 * 3600, maxEntries: 200 }),
    ],
  })
)

// Transaksi — network first
registerRoute(
  ({ url }) => url.pathname.includes('/api/v1/transactions'),
  new NetworkFirst({
    cacheName: 'transactions-cache',
    plugins: [
      new BackgroundSyncPlugin('transactions-queue', {
        maxRetentionTime: 24 * 60, // 24 jam
      }),
    ],
  })
)

// Static assets — cache first, 30 hari
registerRoute(
  ({ request }) => ['style', 'script', 'font'].includes(request.destination),
  new CacheFirst({
    cacheName: 'static-cache',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 30 * 24 * 3600 }),
    ],
  })
)
