from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.schemas.stock import StockAdjustRequest, StockResponse, StockTransferRequest

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("", response_model=list[StockResponse])
async def get_stock(branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(f"""
        SELECT s.product_id, s.variant_id, s.min_qty,
               s.qty + COALESCE(SUM(sm.delta), 0) AS qty
        FROM {branch_schema}.stock s
        LEFT JOIN {branch_schema}.stock_movements sm ON sm.product_id = s.product_id
        GROUP BY s.product_id, s.variant_id, s.min_qty, s.qty
    """))
    rows = result.mappings().all()
    return [StockResponse(
        product_id=r["product_id"],
        variant_id=r["variant_id"],
        qty=r["qty"],
        min_qty=r["min_qty"],
    ) for r in rows]


@router.get("/low")
async def get_low_stock(branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(f"""
        SELECT s.product_id, s.min_qty,
               s.qty + COALESCE(SUM(sm.delta), 0) AS qty
        FROM {branch_schema}.stock s
        LEFT JOIN {branch_schema}.stock_movements sm ON sm.product_id = s.product_id
        GROUP BY s.product_id, s.min_qty, s.qty
        HAVING s.qty + COALESCE(SUM(sm.delta), 0) <= s.min_qty
    """))
    return [dict(r._mapping) for r in result]


@router.get("/{product_id}")
async def get_product_stock(product_id: UUID, branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    stock = await db.execute(text(f"""
        SELECT s.qty + COALESCE(SUM(sm.delta),0) AS current_qty, s.min_qty
        FROM {branch_schema}.stock s
        LEFT JOIN {branch_schema}.stock_movements sm ON sm.product_id=s.product_id
        WHERE s.product_id=:pid
        GROUP BY s.qty, s.min_qty
    """), {"pid": str(product_id)})
    row = stock.mappings().one_or_none()

    movements = await db.execute(text(f"""
        SELECT delta, type, note, created_at FROM {branch_schema}.stock_movements
        WHERE product_id=:pid ORDER BY created_at DESC LIMIT 20
    """), {"pid": str(product_id)})

    return {
        "product_id": str(product_id),
        "current_qty": float(row["current_qty"]) if row else 0,
        "min_qty": float(row["min_qty"]) if row else 5,
        "movements": [dict(m._mapping) for m in movements],
    }


@router.post("/adjust")
async def adjust_stock(data: StockAdjustRequest, db: AsyncSession = Depends(get_db)):
    await db.execute(text(f"""
        INSERT INTO {data.branch_schema}.stock_movements
        (id, product_id, delta, type, note, created_at)
        VALUES (gen_random_uuid(), :pid, :delta, 'adjustment', :note, NOW())
    """), {"pid": str(data.product_id), "delta": data.delta, "note": data.note})
    await db.commit()
    return {"ok": True}


@router.post("/transfer")
async def transfer_stock(data: StockTransferRequest, db: AsyncSession = Depends(get_db)):
    import uuid
    ref = str(uuid.uuid4())
    await db.execute(text(f"""
        INSERT INTO {data.from_schema}.stock_movements
        (id, product_id, delta, type, reference_id, note, created_at)
        VALUES (gen_random_uuid(), :pid, :neg_qty, 'transfer_out', :ref, :note, NOW())
    """), {"pid": str(data.product_id), "neg_qty": -data.qty, "ref": ref, "note": f"Transfer to {data.to_schema}"})

    await db.execute(text(f"""
        INSERT INTO {data.to_schema}.stock_movements
        (id, product_id, delta, type, reference_id, note, created_at)
        VALUES (gen_random_uuid(), :pid, :qty, 'transfer_in', :ref, :note, NOW())
    """), {"pid": str(data.product_id), "qty": data.qty, "ref": ref, "note": f"Transfer from {data.from_schema}"})

    await db.commit()
    return {"transfer_ref": ref, "qty": data.qty, "ok": True}
