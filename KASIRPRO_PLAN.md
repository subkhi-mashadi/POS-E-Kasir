# KasirPro — Rencana Pengembangan Sistem Kasir Multi-Cabang

## Ringkasan

Sistem kasir modern berbasis PWA dengan offline support penuh, sinkronisasi otomatis, dan manajemen terpusat untuk jaringan multi-cabang.

- **Backend:** Python (FastAPI)
- **Frontend:** React + Vite (PWA)
- **Database:** PostgreSQL (schema-per-branch)
- **Cache/Queue:** Redis + Celery
- **Offline:** IndexedDB via Dexie.js + Workbox Service Worker
- **Estimasi:** 17–22 minggu (5 fase)

---

## Tech Stack Detail

### Backend
| Layer | Teknologi | Keterangan |
|-------|-----------|------------|
| API Framework | FastAPI 0.115+ | Async-native, auto OpenAPI docs |
| Database | PostgreSQL 16 | Multi-schema per cabang |
| ORM | SQLAlchemy 2.0 + Alembic | Async ORM + migrations |
| Cache | Redis 7 | Session, rate limit, pub/sub |
| Task Queue | Celery + Redis broker | Background jobs, scheduled tasks |
| Auth | JWT (python-jose) + OAuth2 | Access + refresh token, RBAC |
| Validasi | Pydantic v2 | Request/response schema |
| File Storage | MinIO (S3-compatible) | Foto produk, laporan PDF |
| WebSocket | FastAPI WebSocket | Real-time sync notifikasi |

### Frontend
| Layer | Teknologi | Keterangan |
|-------|-----------|------------|
| Framework | React 18 + Vite | SPA |
| Language | TypeScript | Type safety |
| State Global | Zustand | Ringan, tidak boilerplate |
| Data Fetching | TanStack Query v5 | Cache, sync, mutation |
| Offline DB | Dexie.js (IndexedDB) | Transaksi & produk saat offline |
| PWA | Workbox | Service Worker, background sync |
| Styling | TailwindCSS + shadcn/ui | Komponen siap pakai |
| Form | React Hook Form + Zod | Validasi client-side |
| Print | react-thermal-printer | Struk thermal 58mm / 80mm |

### Infrastruktur
| Komponen | Teknologi | Keterangan |
|----------|-----------|------------|
| Reverse Proxy | Nginx | SSL, rate limit, routing |
| Containerization | Docker + Compose | Dev & prod environment |
| Monitoring | Sentry + Prometheus/Grafana | Error tracking + metrics |
| CI/CD | GitHub Actions | Auto test + deploy |
| Backup | pg_dump → MinIO | Harian otomatis |

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────┐
│                    CLIENT LAYER                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  React PWA  │  │  IndexedDB   │  │  Service   │  │
│  │  (Kasir UI) │  │  (Dexie.js)  │  │  Worker    │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
│         └────────────────┴───────────────-┘          │
└───────────────────────┬─────────────────────────────┘
                        │ HTTPS + WebSocket
┌───────────────────────▼─────────────────────────────┐
│                   API GATEWAY                        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │   FastAPI    │  │  WebSocket   │  │   Nginx   │  │
│  │  REST API    │  │   Handler    │  │   Proxy   │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┘  │
│         └────────────────-┘                          │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                 BACKEND SERVICES                     │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │  Celery   │  │   Redis   │  │     MinIO        │  │
│  │  Workers  │  │   Cache   │  │  File Storage    │  │
│  └───────────┘  └───────────┘  └──────────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                  DATA LAYER                          │
│  ┌──────────────────────┐  ┌────────────────────┐   │
│  │  PostgreSQL Primary  │  │  Read Replica      │   │
│  │  schema: public      │  │  (laporan besar)   │   │
│  │  schema: branch_jkt  │  └────────────────────┘   │
│  │  schema: branch_bdg  │                            │
│  │  schema: branch_sby  │                            │
│  └──────────────────────┘                            │
└─────────────────────────────────────────────────────┘
```

---

## Strategi Offline (PWA)

### Alur Data

```
[Kasir Input] → [IndexedDB lokal] → [Sync Queue] → [FastAPI] → [PostgreSQL]
                    offline               ↑ online kembali
```

### Mekanisme

1. **Install PWA** — Workbox pre-cache: produk, harga, data master cabang
2. **Saat offline** — Transaksi tulis ke IndexedDB dengan:
   - `local_id`: UUID v4 (tidak pernah diganti server)
   - `sync_status`: `pending_sync`
   - `created_at`: timestamp lokal
3. **Sync queue** — Background Sync API otomatis trigger saat online
4. **Conflict resolution**:
   - Transaksi: last-write-wins (setiap transaksi unik per `local_id`)
   - Stok: simpan sebagai delta `±qty`, server gabungkan semua delta
   - Produk: server versi lebih tinggi menang, kasir terima notif update
5. **Retry policy** — Max 3 retries, exponential backoff (1s, 2s, 4s)
6. **Gagal sync** — Tetap `pending_sync`, retry di session berikutnya

### Cache Strategy (Workbox)

| Resource | Strategy | TTL |
|----------|----------|-----|
| Produk & harga | StaleWhileRevalidate | 1 jam |
| Gambar produk | CacheFirst | 7 hari |
| API transaksi | NetworkFirst | — |
| Static assets | CacheFirst | 30 hari |

---

## Arsitektur Multi-Cabang

### Strategi: Schema-per-Branch di PostgreSQL

```sql
-- Schema public: data master global
public.branches
public.products
public.categories
public.users (superadmin)

-- Schema per cabang: data operasional
branch_jakarta.transactions
branch_jakarta.transaction_items
branch_jakarta.stock_movements
branch_jakarta.users (kasir + admin cabang)
branch_jakarta.stock

-- Laporan konsolidasi via cross-schema query
SELECT b.name, SUM(t.total)
FROM branches b
JOIN branch_jakarta.transactions t ON ...
UNION ALL
JOIN branch_bandung.transactions t ON ...
```

### Role Hierarchy

```
superadmin          → akses semua cabang, setting global
  └── admin_cabang  → akses 1 cabang, CRUD produk lokal
        └── supervisor → void transaksi, diskon manual
              └── kasir → transaksi saja
```

---

## Skema Database

### Tabel Utama (schema: public)

```sql
branches (id, name, code, schema_name, address, is_active, created_at)
products (id, sku, name, category_id, base_price, cost_price, barcode, variants jsonb, image_url, is_active)
categories (id, name, parent_id, sort_order)
users (id, branch_id, name, email, password_hash, role, permissions jsonb, is_active)
promotions (id, name, type, conditions jsonb, discount_value, start_at, end_at)
customers (id, name, phone, email, points, tier, branch_id)
suppliers (id, name, phone, address, is_active)
```

### Tabel Operasional (schema: per cabang)

```sql
transactions (
  id uuid PK,
  local_id uuid UNIQUE,          -- UUID dari client, tidak berubah
  invoice_no varchar,
  cashier_id uuid → users,
  customer_id uuid → customers,
  subtotal decimal,
  discount decimal,
  tax decimal,
  total decimal,
  payment_method varchar,        -- cash | qris | transfer | debit | credit | split
  payment_detail jsonb,
  sync_status varchar,           -- pending_sync | synced | failed
  synced_at timestamptz,
  created_at timestamptz
)

transaction_items (
  id, transaction_id, product_id, variant_id,
  qty, unit_price, discount, subtotal
)

stock (
  id, product_id, variant_id, qty, min_qty, location
)

stock_movements (
  id, product_id, delta, type,   -- sale | purchase | adjustment | transfer_in | transfer_out
  reference_id, note, created_by, created_at
)

shifts (
  id, cashier_id, opening_balance, closing_balance,
  opened_at, closed_at, status
)

purchase_orders (
  id, supplier_id, status, items jsonb, total, received_at
)
```

---

## API Endpoints

### Auth
```
POST   /auth/login              Login, return access + refresh token
POST   /auth/refresh            Refresh access token
POST   /auth/logout             Revoke refresh token
```

### Transaksi
```
POST   /transactions            Buat transaksi baru
POST   /transactions/sync       Bulk sync offline (terima array local_id)
GET    /transactions            List (filter: date, cashier, status)
GET    /transactions/{id}       Detail + items
POST   /transactions/{id}/void  Void transaksi (supervisor+)
GET    /transactions/{id}/receipt  Data struk untuk print
```

### Produk
```
GET    /products                List + stok (filter, search, pagination)
GET    /products/sync?since=ts  Produk berubah sejak timestamp (cache refresh)
GET    /products/barcode/{code} Lookup via barcode — endpoint cepat
POST   /products                Buat produk baru (admin+)
PUT    /products/{id}           Update produk
DELETE /products/{id}           Soft delete
```

### Stok
```
GET    /stock                   Stok semua produk cabang ini
GET    /stock/{product_id}      Stok + history mutasi
POST   /stock/adjust            Penyesuaian manual (supervisor+)
POST   /stock/transfer          Transfer antar cabang (admin+)
GET    /stock/low               Produk stok < minimum
```

### Pelanggan
```
GET    /customers               List pelanggan
POST   /customers               Daftar pelanggan baru
GET    /customers/{id}          Detail + histori transaksi + poin
PUT    /customers/{id}          Update data pelanggan
POST   /customers/{id}/points   Tambah/kurang poin manual
```

### Laporan
```
GET    /reports/sales           Penjualan (filter: branch, date range)
GET    /reports/products        Laporan produk terlaris / terlamban
GET    /reports/cashier         Performa kasir per shift
GET    /reports/stock           Laporan stok + valuasi
GET    /reports/consolidated    Gabungan semua cabang (superadmin only)
GET    /reports/export          Export PDF / Excel
```

### Multi-Cabang (Superadmin)
```
GET    /branches                List semua cabang
POST   /branches                Buat cabang baru (auto-provision schema)
PUT    /branches/{id}           Update setting cabang
GET    /branches/{id}/dashboard Dashboard real-time per cabang
POST   /branches/sync-products  Sinkronisasi produk master ke semua cabang
```

---

## Struktur Project

### Backend (Python)
```
kasirpro-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── transactions.py
│   │   │   ├── products.py
│   │   │   ├── stock.py
│   │   │   ├── customers.py
│   │   │   ├── reports.py
│   │   │   └── branches.py
│   │   └── websocket.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py       # multi-schema session factory
│   │   └── redis.py
│   ├── models/
│   │   ├── public/           # global tables
│   │   └── branch/           # per-branch tables
│   ├── schemas/              # Pydantic models
│   ├── services/
│   │   ├── sync_service.py   # conflict resolution logic
│   │   ├── stock_service.py  # delta-based stock
│   │   └── report_service.py
│   ├── workers/              # Celery tasks
│   │   ├── sync_worker.py
│   │   ├── report_worker.py
│   │   └── notification_worker.py
│   └── main.py
├── alembic/                  # DB migrations
├── tests/
├── docker/
├── requirements.txt
└── docker-compose.yml
```

### Frontend (React)
```
kasirpro-web/
├── public/
│   ├── manifest.json         # PWA manifest
│   └── sw.js                 # Service worker entry
├── src/
│   ├── pages/
│   │   ├── pos/              # Halaman kasir utama
│   │   ├── products/
│   │   ├── stock/
│   │   ├── customers/
│   │   ├── reports/
│   │   └── settings/
│   ├── components/
│   │   ├── pos/              # Komponen kasir
│   │   └── ui/               # shadcn/ui components
│   ├── stores/               # Zustand stores
│   ├── hooks/
│   │   ├── useOfflineSync.ts  # sync logic
│   │   └── useNetworkStatus.ts
│   ├── lib/
│   │   ├── db.ts             # Dexie IndexedDB schema
│   │   ├── sync.ts           # Background sync queue
│   │   └── api.ts            # Axios instance
│   └── workers/
│       └── service-worker.ts  # Workbox config
├── vite.config.ts
└── package.json
```

---

## Roadmap

### Fase 1 — Foundation (3–4 minggu)
- [ ] Setup repo monorepo / separate repos
- [ ] Docker Compose: FastAPI + PostgreSQL + Redis + MinIO + Nginx
- [ ] Multi-schema PostgreSQL setup + Alembic
- [ ] Auth endpoint: login, refresh, logout
- [ ] RBAC middleware
- [ ] React + Vite + TypeScript boilerplate
- [ ] TailwindCSS + shadcn/ui setup
- [ ] GitHub Actions CI (lint, test, build)

### Fase 2 — Core POS (4–5 minggu)
- [ ] CRUD produk + kategori + varian
- [ ] Manajemen stok dasar (delta-based)
- [ ] UI kasir: cart, search produk, scan barcode
- [ ] Proses transaksi: payment, kembalian
- [ ] Multiple payment method
- [ ] Open/close shift dengan saldo kas
- [ ] Print struk thermal (58mm/80mm)
- [ ] Dashboard admin cabang dasar

### Fase 3 — PWA & Offline (3–4 minggu)
- [ ] Dexie.js schema: transactions, products, customers
- [ ] Workbox setup: cache strategies per resource type
- [ ] Background Sync API integration
- [ ] Conflict resolution engine (delta stock, UUID preservation)
- [ ] Offline indicator + pending sync counter di UI
- [ ] PWA install prompt & manifest
- [ ] Pre-cache produk + harga saat install
- [ ] Test offline → sync flow end-to-end

### Fase 4 — Multi-Cabang & Fitur Lanjutan (4–5 minggu)
- [ ] Dashboard pusat semua cabang (superadmin)
- [ ] Provision cabang baru (auto-create schema)
- [ ] Transfer stok antar cabang
- [ ] Sinkronisasi produk master → semua cabang
- [ ] Manajemen pelanggan + poin loyalty
- [ ] Diskon & promosi (jadwal, happy hour, buy X get Y)
- [ ] Voucher & kupon
- [ ] Manajemen supplier + purchase order
- [ ] Retur ke supplier
- [ ] Manajemen karyawan + komisi

### Fase 5 — Analytics & Launch (3–4 minggu)
- [ ] Dashboard analytics lengkap (grafik, tren)
- [ ] Laporan konsolidasi lintas cabang
- [ ] Export laporan PDF + Excel (Celery background)
- [ ] Push notification (stok menipis, laporan harian)
- [ ] Kirim struk digital via WhatsApp (WA Business API / wa-automate)
- [ ] Performance audit (Lighthouse, query optimization)
- [ ] Security hardening (rate limit, audit log, pen test checklist)
- [ ] Production deployment + monitoring setup

---

## Keputusan Teknis Kritis

### 1. UUID Lokal Tidak Pernah Diganti Server
Setiap transaksi offline mendapat `local_id` (UUID v4) dari client. Server menyimpan `local_id` ini apa adanya — tidak generate ulang. Ini memastikan:
- Tidak ada duplikasi jika sync dikirim dua kali
- Audit trail utuh dari client ke server
- Idempotent sync: kirim ulang payload yang sama tidak membuat transaksi ganda

### 2. Stok Sebagai Delta, Bukan Absolut
Mutasi stok disimpan sebagai `delta` (±), bukan nilai akhir. Contoh:
```
Jual 3 pcs → delta: -3
Terima barang 10 pcs → delta: +10
Stok akhir = SUM(delta) WHERE product_id = X
```
Keuntungan: tidak ada konflik "siapa yang benar" saat dua kasir offline bersamaan jual produk yang sama.

### 3. Schema-per-Branch vs Row-Level Tenancy
Dipilih schema-per-branch karena:
- Isolasi data lebih kuat (tidak ada risiko cross-branch query bocor)
- Query laporan per cabang lebih cepat (tidak perlu filter `branch_id` di setiap tabel)
- Mudah backup/restore per cabang
- Cross-schema query untuk konsolidasi tetap bisa dengan PostgreSQL `SET search_path`

### 4. Workbox Cache Strategy per Resource
Tidak semua resource sama pentingnya saat offline:
- **Produk & harga** → StaleWhileRevalidate: kasir dapat data lama tapi tetap bisa beroperasi
- **Gambar** → CacheFirst: tidak perlu fresh setiap saat
- **Transaksi** → NetworkFirst: selalu coba ke server dulu, fallback ke IndexedDB

---

## Estimasi Waktu Total

| Fase | Durasi |
|------|--------|
| Fase 1 — Foundation | 3–4 minggu |
| Fase 2 — Core POS | 4–5 minggu |
| Fase 3 — PWA & Offline | 3–4 minggu |
| Fase 4 — Multi-Cabang & Fitur | 4–5 minggu |
| Fase 5 — Analytics & Launch | 3–4 minggu |
| **Total** | **17–22 minggu** |

*Estimasi untuk 2 developer (1 BE + 1 FE). Bisa dipercepat dengan tambah developer di fase 2–4.*

---

## Checklist Sebelum Mulai Coding

- [ ] Tentukan nama domain + SSL cert
- [ ] Pilih cloud provider / VPS (minimal 4 vCPU, 8GB RAM, 100GB SSD)
- [ ] Setup PostgreSQL production (atau managed DB)
- [ ] Buat repo GitHub (mono atau separate)
- [ ] Tentukan printer thermal yang didukung (58mm / 80mm)
- [ ] Tentukan payment gateway untuk QRIS (Midtrans / Xendit / langsung acquirer)
- [ ] Konfirmasi apakah perlu integrasi WhatsApp untuk struk digital
- [ ] Definisi final role & permission per jenis pengguna
