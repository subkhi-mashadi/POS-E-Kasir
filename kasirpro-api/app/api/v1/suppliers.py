from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.models.public.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierResponse, PurchaseOrderCreate

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierResponse])
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.is_active == True))
    return result.scalars().all()


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(data: SupplierCreate, db: AsyncSession = Depends(get_db)):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(supplier_id: UUID, data: SupplierCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(supplier, k, v)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(supplier_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    supplier.is_active = False
    await db.commit()


# Purchase Orders
@router.post("/{supplier_id}/purchase-orders")
async def create_po(
    supplier_id: UUID,
    data: PurchaseOrderCreate,
    branch_schema: str = "public",
    db: AsyncSession = Depends(get_db)
):
    import json, uuid
    po_id = str(uuid.uuid4())
    total = sum(item["qty"] * item["unit_cost"] for item in data.items)
    await db.execute(text(f"""
        INSERT INTO {branch_schema}.purchase_orders
        (id, supplier_id, status, items, total, created_at)
        VALUES (:id, :sid, 'draft', :items::jsonb, :total, NOW())
    """), {
        "id": po_id,
        "sid": str(supplier_id),
        "items": json.dumps(data.items),
        "total": total,
    })
    await db.commit()
    return {"po_id": po_id, "total": total, "status": "draft"}


@router.post("/{supplier_id}/purchase-orders/{po_id}/receive")
async def receive_po(
    supplier_id: UUID,
    po_id: UUID,
    branch_schema: str = "public",
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(f"SELECT items FROM {branch_schema}.purchase_orders WHERE id=:id AND supplier_id=:sid"),
        {"id": str(po_id), "sid": str(supplier_id)}
    )
    row = result.mappings().one_or_none()
    if not row:
        raise HTTPException(404, "Purchase order not found")

    import json
    items = row["items"] if isinstance(row["items"], list) else json.loads(row["items"])
    for item in items:
        await db.execute(text(f"""
            INSERT INTO {branch_schema}.stock_movements
            (id, product_id, delta, type, reference_id, created_at)
            VALUES (gen_random_uuid(), :pid, :delta, 'purchase', :ref, NOW())
        """), {"pid": item["product_id"], "delta": item["qty"], "ref": str(po_id)})

    await db.execute(
        text(f"UPDATE {branch_schema}.purchase_orders SET status='received', received_at=NOW() WHERE id=:id"),
        {"id": str(po_id)}
    )
    await db.commit()
    return {"po_id": str(po_id), "status": "received"}


@router.get("/{supplier_id}/purchase-orders")
async def list_pos(supplier_id: UUID, branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text(f"SELECT * FROM {branch_schema}.purchase_orders WHERE supplier_id=:sid ORDER BY created_at DESC"),
        {"sid": str(supplier_id)}
    )
    return [dict(r._mapping) for r in result]
