from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import json
import uuid as uuid_module
from app.core.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse, SyncTransactionRequest

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db)):
    schema = data.branch_schema
    tx_id = str(uuid_module.uuid4())
    invoice_no = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    await db.execute(text(f"""
        INSERT INTO {schema}.transactions
        (id, local_id, invoice_no, cashier_id, customer_id,
         subtotal, discount, tax, total,
         payment_method, payment_detail, sync_status, synced_at, created_at)
        VALUES (:id, :local_id, :invoice_no, :cashier_id, :customer_id,
                :subtotal, :discount, :tax, :total,
                :payment_method, :payment_detail::jsonb,
                'synced', NOW(), :created_at)
    """), {
        "id": tx_id,
        "local_id": str(data.local_id),
        "invoice_no": invoice_no,
        "cashier_id": str(data.cashier_id),
        "customer_id": str(data.customer_id) if data.customer_id else None,
        "subtotal": float(data.subtotal),
        "discount": float(data.discount),
        "tax": float(data.tax),
        "total": float(data.total),
        "payment_method": data.payment_method,
        "payment_detail": json.dumps(data.payment_detail),
        "created_at": data.created_at or datetime.now(timezone.utc).isoformat(),
    })

    for item in data.items:
        await db.execute(text(f"""
            INSERT INTO {schema}.transaction_items
            (id, transaction_id, product_id, qty, unit_price, discount, subtotal)
            VALUES (gen_random_uuid(), :tx_id, :product_id, :qty, :unit_price, :discount, :subtotal)
        """), {
            "tx_id": tx_id,
            "product_id": str(item.product_id),
            "qty": item.qty,
            "unit_price": float(item.unit_price),
            "discount": float(item.discount),
            "subtotal": float(item.subtotal),
        })

        await db.execute(text(f"""
            INSERT INTO {schema}.stock_movements
            (id, product_id, delta, type, reference_id, created_at)
            VALUES (gen_random_uuid(), :product_id, :delta, 'sale', :ref, NOW())
        """), {"product_id": str(item.product_id), "delta": -item.qty, "ref": tx_id})

    await db.commit()
    return TransactionResponse(
        id=UUID(tx_id),
        local_id=data.local_id,
        invoice_no=invoice_no,
        total=data.total,
        sync_status="synced",
    )


@router.post("/sync")
async def sync_transactions(payload: SyncTransactionRequest, db: AsyncSession = Depends(get_db)):
    results = []
    for tx in payload.transactions:
        result = await db.execute(
            text(f"SELECT id FROM {payload.branch_schema}.transactions WHERE local_id = :lid"),
            {"lid": str(tx.local_id)},
        )
        existing = result.scalar_one_or_none()
        if existing:
            results.append({"local_id": str(tx.local_id), "status": "already_synced"})
            continue
        resp = await create_transaction(tx, db)
        results.append({"local_id": str(tx.local_id), "status": "synced", "id": str(resp.id)})
    return {"results": results}


@router.get("")
async def list_transactions(
    branch_schema: str = "public",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    cashier_id: Optional[UUID] = None,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    filters, params = [], {}
    if date_from:
        filters.append("created_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        filters.append("created_at <= :date_to")
        params["date_to"] = date_to
    if cashier_id:
        filters.append("cashier_id = :cashier_id")
        params["cashier_id"] = str(cashier_id)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    result = await db.execute(
        text(f"""
            SELECT * FROM {branch_schema}.transactions
            {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        {**params, "limit": per_page, "offset": (page - 1) * per_page},
    )
    rows = result.mappings().all()
    return [
        {k: v.isoformat() if hasattr(v, "isoformat") else str(v) if isinstance(v, UUID) else v
         for k, v in dict(r).items()}
        for r in rows
    ]


@router.get("/{tx_id}/receipt")
async def get_receipt(tx_id: UUID, branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(f"SELECT * FROM {branch_schema}.transactions WHERE id = :id"),
        {"id": str(tx_id)},
    )
    tx = result.mappings().one_or_none()
    if not tx:
        raise HTTPException(404, "Transaction not found")

    items_result = await db.execute(
        text(f"""
            SELECT ti.*, p.name AS product_name
            FROM {branch_schema}.transaction_items ti
            JOIN public.products p ON p.id = ti.product_id
            WHERE ti.transaction_id = :id
        """),
        {"id": str(tx_id)},
    )
    items = [dict(r._mapping) for r in items_result]

    return {
        "transaction": {
            k: v.isoformat() if hasattr(v, "isoformat") else str(v) for k, v in dict(tx).items()
        },
        "items": [
            {k: str(v) if isinstance(v, UUID) else v for k, v in item.items()}
            for item in items
        ],
    }


@router.post("/{tx_id}/receipt/send-whatsapp")
async def send_receipt_whatsapp(
    tx_id: UUID,
    phone: str,
    branch_schema: str = "public",
    cashier_name: str = "Kasir",
    branch_name: str = "KasirPro",
    db: AsyncSession = Depends(get_db),
):
    """Kirim struk ke nomor WhatsApp via Fonnte."""
    # Ambil data transaksi
    tx_result = await db.execute(
        text(f"SELECT * FROM {branch_schema}.transactions WHERE id = :id"),
        {"id": str(tx_id)},
    )
    tx = tx_result.mappings().one_or_none()
    if not tx:
        raise HTTPException(404, "Transaction not found")

    items_result = await db.execute(
        text(f"""
            SELECT ti.qty, ti.unit_price, ti.subtotal, p.name AS product_name
            FROM {branch_schema}.transaction_items ti
            JOIN public.products p ON p.id = ti.product_id
            WHERE ti.transaction_id = :id
        """),
        {"id": str(tx_id)},
    )
    items = [dict(r._mapping) for r in items_result]

    from app.services.notification_service import send_whatsapp_receipt
    success = await send_whatsapp_receipt(
        phone=phone,
        invoice_no=tx["invoice_no"],
        items=items,
        total=float(tx["total"]),
        payment_method=tx["payment_method"],
        cashier_name=cashier_name,
        branch_name=branch_name,
    )

    if not success:
        raise HTTPException(502, "Gagal mengirim WhatsApp. Cek konfigurasi Fonnte.")

    return {"ok": True, "phone": phone, "invoice_no": tx["invoice_no"]}


@router.post("/{tx_id}/void")
async def void_transaction(tx_id: UUID, branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(f"SELECT id FROM {branch_schema}.transactions WHERE id = :id"),
        {"id": str(tx_id)},
    )
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Transaction not found")

    items_result = await db.execute(
        text(f"SELECT product_id, qty FROM {branch_schema}.transaction_items WHERE transaction_id = :id"),
        {"id": str(tx_id)},
    )
    for item in items_result:
        await db.execute(
            text(f"""
                INSERT INTO {branch_schema}.stock_movements
                (id, product_id, delta, type, reference_id, created_at)
                VALUES (gen_random_uuid(), :pid, :delta, 'void', :ref, NOW())
            """),
            {"pid": str(item.product_id), "delta": item.qty, "ref": str(tx_id)},
        )

    await db.execute(
        text(f"UPDATE {branch_schema}.transactions SET sync_status='void' WHERE id = :id"),
        {"id": str(tx_id)},
    )
    await db.commit()
    return {"ok": True}
