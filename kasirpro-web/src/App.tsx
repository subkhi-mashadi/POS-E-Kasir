import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useOfflineSync } from './hooks/useOfflineSync'
import InstallBanner from './components/ui/InstallBanner'
import SyncBadge from './components/ui/SyncBadge'
import LoginPage from './pages/auth/LoginPage'
import PosPage from './pages/pos/PosPage'
import ProductsPage from './pages/products/ProductsPage'
import SyncPage from './pages/sync/SyncPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import CustomersPage from './pages/customers/CustomersPage'
import PromotionsPage from './pages/promotions/PromotionsPage'
import ReportsPage from './pages/reports/ReportsPage'
import SettingsPage from './pages/settings/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 60_000, gcTime: 5 * 60_000 },
  },
})

const NAV_LINKS = [
  { to: '/pos', label: 'Kasir' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/reports', label: 'Laporan' },
  { to: '/products', label: 'Produk' },
  { to: '/customers', label: 'Pelanggan' },
  { to: '/promotions', label: 'Promosi' },
  { to: '/sync', label: 'Sync' },
  { to: '/settings', label: '⚙️' },
]

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b px-4 py-2 flex items-center gap-1 overflow-x-auto">
        <span className="font-bold text-blue-600 mr-3 whitespace-nowrap">KasirPro</span>
        {NAV_LINKS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `px-3 py-1.5 rounded text-sm whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-medium'
                  : 'text-gray-500 hover:text-gray-900'
              }`
            }
          >
            {label}
          </NavLink>
        ))}
        <div className="ml-auto pl-4">
          <SyncBadge />
        </div>
      </nav>
      {children}
    </div>
  )
}

function AppInner() {
  useOfflineSync()
  return (
    <BrowserRouter>
      <InstallBanner />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/pos" element={<PosPage />} />
        <Route path="/dashboard" element={<Layout><DashboardPage /></Layout>} />
        <Route path="/reports" element={<Layout><ReportsPage /></Layout>} />
        <Route path="/products" element={<Layout><ProductsPage /></Layout>} />
        <Route path="/customers" element={<Layout><CustomersPage /></Layout>} />
        <Route path="/promotions" element={<Layout><PromotionsPage /></Layout>} />
        <Route path="/sync" element={<Layout><SyncPage /></Layout>} />
        <Route path="/settings" element={<Layout><SettingsPage /></Layout>} />
        <Route path="*" element={<Navigate to="/pos" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  )
}
