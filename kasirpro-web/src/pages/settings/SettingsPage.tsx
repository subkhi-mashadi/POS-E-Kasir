import { useState } from 'react'

export default function SettingsPage() {
  const [telegramToken, setTelegramToken] = useState('')
  const [telegramChatId, setTelegramChatId] = useState('')
  const [fonnteToken, setFonnteToken] = useState('')
  const [saved, setSaved] = useState(false)

  function handleSave() {
    // Di production: kirim ke backend endpoint PATCH /settings
    // Untuk sekarang: tampilkan instruksi update .env
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold mb-6">Pengaturan Integrasi</h1>

      {/* Telegram */}
      <div className="bg-white border rounded-xl p-5 mb-4">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">✈️</span>
          <div>
            <div className="font-semibold">Telegram Bot</div>
            <div className="text-xs text-gray-500">Notifikasi stok menipis & laporan harian</div>
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Bot Token</label>
            <input
              type="password"
              placeholder="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
              value={telegramToken}
              onChange={e => setTelegramToken(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">Dapatkan dari @BotFather di Telegram</p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Chat ID</label>
            <input
              type="text"
              placeholder="-1001234567890"
              value={telegramChatId}
              onChange={e => setTelegramChatId(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">Chat ID grup/channel. Gunakan @userinfobot untuk cek.</p>
          </div>
        </div>
      </div>

      {/* Fonnte */}
      <div className="bg-white border rounded-xl p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">💬</span>
          <div>
            <div className="font-semibold">Fonnte WhatsApp</div>
            <div className="text-xs text-gray-500">Kirim struk digital via WhatsApp</div>
          </div>
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Fonnte Token</label>
          <input
            type="password"
            placeholder="Token dari dashboard.fonnte.com"
            value={fonnteToken}
            onChange={e => setFonnteToken(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm font-mono"
          />
          <p className="text-xs text-gray-400 mt-1">
            Daftar di <span className="text-blue-500">fonnte.com</span> → Device → Copy Token
          </p>
        </div>
      </div>

      {/* Instruksi */}
      <div className="bg-gray-50 border rounded-xl p-4 mb-6 text-sm">
        <div className="font-semibold mb-2">Cara setup:</div>
        <ol className="list-decimal list-inside space-y-1 text-gray-600">
          <li>Isi nilai di atas</li>
          <li>Update file <code className="bg-gray-200 px-1 rounded">kasirpro-api/.env</code> dengan nilai tersebut</li>
          <li>Restart API: <code className="bg-gray-200 px-1 rounded">docker-compose restart api celery-worker celery-beat</code></li>
        </ol>
        <div className="mt-3 bg-gray-100 rounded p-2 font-mono text-xs whitespace-pre">
{`TELEGRAM_BOT_TOKEN=${telegramToken || 'YOUR_BOT_TOKEN'}
TELEGRAM_CHAT_ID=${telegramChatId || 'YOUR_CHAT_ID'}
FONNTE_TOKEN=${fonnteToken || 'YOUR_FONNTE_TOKEN'}`}
        </div>
      </div>

      <button
        onClick={handleSave}
        className="w-full py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
      >
        {saved ? '✓ Disimpan' : 'Simpan & Tampilkan Config'}
      </button>
    </div>
  )
}
