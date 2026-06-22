import { usePWAInstall } from '../../hooks/usePWAInstall'

export default function InstallBanner() {
  const { canInstall, triggerInstall } = usePWAInstall()

  if (!canInstall) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-blue-600 text-white px-4 py-3 flex items-center justify-between z-50 shadow-lg">
      <div>
        <div className="font-semibold text-sm">Install KasirPro</div>
        <div className="text-xs text-blue-200">Akses lebih cepat &amp; bisa dipakai offline</div>
      </div>
      <div className="flex gap-2">
        <button
          onClick={triggerInstall}
          className="bg-white text-blue-600 px-4 py-1.5 rounded-lg text-sm font-semibold hover:bg-blue-50"
        >
          Install
        </button>
      </div>
    </div>
  )
}
