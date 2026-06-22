import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_telegram(message: str) -> bool:
    """Send message to Telegram channel/group."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — skip notification")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


async def send_whatsapp_receipt(
    phone: str,
    invoice_no: str,
    items: list[dict],
    total: float,
    payment_method: str,
    cashier_name: str,
    branch_name: str,
) -> bool:
    """
    Kirim struk via Fonnte WhatsApp API.
    phone format: 628xxxxxxxxx (tanpa + atau 0 di depan)
    """
    if not settings.FONNTE_TOKEN:
        logger.warning("Fonnte not configured — skip WhatsApp receipt")
        return False

    # Format struk
    lines = [
        f"🧾 *STRUK BELANJA*",
        f"📍 {branch_name}",
        f"━━━━━━━━━━━━━━━━━━",
        f"No. Invoice: {invoice_no}",
        f"Kasir: {cashier_name}",
        f"━━━━━━━━━━━━━━━━━━",
    ]
    for item in items:
        name = item.get("product_name", "Produk")
        qty = item.get("qty", 1)
        price = item.get("unit_price", 0)
        subtotal = item.get("subtotal", qty * price)
        lines.append(f"{name}")
        lines.append(f"  {qty} x Rp {int(price):,} = Rp {int(subtotal):,}".replace(",", "."))

    lines += [
        f"━━━━━━━━━━━━━━━━━━",
        f"*Total: Rp {int(total):,}*".replace(",", "."),
        f"Bayar: {payment_method.upper()}",
        f"━━━━━━━━━━━━━━━━━━",
        f"Terima kasih telah berbelanja! 🙏",
    ]

    message = "\n".join(lines)
    payload = {
        "target": phone,
        "message": message,
        "countryCode": "62",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                settings.FONNTE_API_URL,
                data=payload,
                headers={"Authorization": settings.FONNTE_TOKEN},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("status") is False:
                logger.error("Fonnte error: %s", result)
                return False
            return True
    except Exception as e:
        logger.error("Fonnte send failed: %s", e)
        return False


async def send_low_stock_alert(branch_name: str, low_items: list[dict]) -> bool:
    """Kirim alert stok menipis ke Telegram."""
    if not low_items:
        return True

    lines = [
        f"⚠️ <b>STOK MENIPIS — {branch_name}</b>",
        f"",
    ]
    for item in low_items:
        name = item.get("name", "?")
        sku = item.get("sku", "?")
        qty = item.get("current_qty", 0)
        min_qty = item.get("min_qty", 0)
        lines.append(f"• <b>{name}</b> (SKU: {sku})")
        lines.append(f"  Stok: {qty} / Min: {min_qty}")

    lines += ["", f"Segera lakukan pengisian stok."]
    return await send_telegram("\n".join(lines))


async def send_daily_report_telegram(summary: list[dict], grand_total: float) -> bool:
    """Kirim laporan harian ke Telegram."""
    lines = [
        f"📊 <b>LAPORAN HARIAN KASIRPRO</b>",
        f"",
    ]
    for branch in summary:
        sales = branch.get("sales", 0)
        count = branch.get("count", 0)
        name = branch.get("branch", "?")
        lines.append(f"🏪 <b>{name}</b>")
        lines.append(f"  Transaksi: {count} | Total: Rp {int(sales):,}".replace(",", "."))

    lines += [
        f"",
        f"━━━━━━━━━━━━━━",
        f"<b>TOTAL: Rp {int(grand_total):,}</b>".replace(",", "."),
    ]
    return await send_telegram("\n".join(lines))
