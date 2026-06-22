from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.models.public.branch import Branch
from app.schemas.branch import BranchCreate, BranchResponse

router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("", response_model=list[BranchResponse])
async def list_branches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    return result.scalars().all()


@router.post("", response_model=BranchResponse, status_code=201)
async def create_branch(data: BranchCreate, db: AsyncSession = Depends(get_db)):
    branch = Branch(**data.model_dump())
    db.add(branch)
    await db.flush()
    await _provision_schema(db, branch.schema_name)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(branch_id: UUID, data: BranchCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(404, "Branch not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(branch, k, v)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.get("/consolidated")
async def consolidated_dashboard(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = result.scalars().all()
    data = []
    for b in branches:
        s = b.schema_name
        try:
            sales = await db.execute(text(
                f"SELECT COALESCE(SUM(total),0) FROM {s}.transactions WHERE DATE(created_at)=CURRENT_DATE AND sync_status!='void'"
            ))
            count = await db.execute(text(
                f"SELECT COUNT(*) FROM {s}.transactions WHERE DATE(created_at)=CURRENT_DATE AND sync_status!='void'"
            ))
            data.append({
                "branch_id": str(b.id),
                "branch_name": b.name,
                "today_sales": float(sales.scalar() or 0),
                "today_transactions": int(count.scalar() or 0),
            })
        except Exception:
            data.append({"branch_id": str(b.id), "branch_name": b.name, "today_sales": 0, "today_transactions": 0})
    total_sales = sum(d["today_sales"] for d in data)
    return {"branches": data, "total_today_sales": total_sales}


@router.get("/{branch_id}/dashboard")
async def branch_dashboard(branch_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(404, "Branch not found")
    s = branch.schema_name

    today_sales = await db.execute(text(
        f"SELECT COALESCE(SUM(total),0) FROM {s}.transactions WHERE DATE(created_at)=CURRENT_DATE AND sync_status!='void'"
    ))
    today_count = await db.execute(text(
        f"SELECT COUNT(*) FROM {s}.transactions WHERE DATE(created_at)=CURRENT_DATE AND sync_status!='void'"
    ))
    low_stock = await db.execute(text(
        f"SELECT COUNT(*) FROM {s}.stock WHERE qty <= min_qty"
    ))
    pending_sync = await db.execute(text(
        f"SELECT COUNT(*) FROM {s}.transactions WHERE sync_status='pending_sync'"
    ))

    return {
        "branch_id": str(branch_id),
        "branch_name": branch.name,
        "today_sales": float(today_sales.scalar() or 0),
        "today_transactions": int(today_count.scalar() or 0),
        "low_stock_count": int(low_stock.scalar() or 0),
        "pending_sync": int(pending_sync.scalar() or 0),
    }


@router.post("/sync-products")
async def sync_products_to_all(db: AsyncSession = Depends(get_db)):
    from app.models.public.product import Product
    products_result = await db.execute(select(Product).where(Product.is_active == True))
    products = products_result.scalars().all()

    branches_result = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = branches_result.scalars().all()

    synced = 0
    for branch in branches:
        for product in products:
            existing = await db.execute(text(
                f"SELECT id FROM {branch.schema_name}.stock WHERE product_id=:pid"
            ), {"pid": str(product.id)})
            if not existing.scalar_one_or_none():
                await db.execute(text(
                    f"INSERT INTO {branch.schema_name}.stock (id,product_id,qty,min_qty) VALUES (gen_random_uuid(),:pid,0,5)"
                ), {"pid": str(product.id)})
                synced += 1
    await db.commit()
    return {"synced_stock_rows": synced}


@router.post("/{branch_id}/shifts/open")
async def open_shift(
    branch_id: UUID,
    opening_balance: float = Body(...),
    cashier_id: UUID = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(404, "Branch not found")
    import uuid
    shift_id = str(uuid.uuid4())
    await db.execute(text(
        f"INSERT INTO {branch.schema_name}.shifts (id,cashier_id,opening_balance,opened_at,status) VALUES (:id,:cid,:bal,NOW(),'open')"
    ), {"id": shift_id, "cid": str(cashier_id), "bal": opening_balance})
    await db.commit()
    return {"shift_id": shift_id, "status": "open"}


@router.post("/{branch_id}/shifts/{shift_id}/close")
async def close_shift(
    branch_id: UUID, shift_id: UUID,
    closing_balance: float = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(404, "Branch not found")
    await db.execute(text(
        f"UPDATE {branch.schema_name}.shifts SET closing_balance=:bal,closed_at=NOW(),status='closed' WHERE id=:id"
    ), {"bal": closing_balance, "id": str(shift_id)})
    await db.commit()
    return {"shift_id": str(shift_id), "status": "closed"}


async def _provision_schema(db: AsyncSession, schema_name: str):
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.transactions (
            id UUID PRIMARY KEY,
            local_id UUID UNIQUE NOT NULL,
            invoice_no VARCHAR(50),
            cashier_id UUID NOT NULL,
            customer_id UUID,
            subtotal NUMERIC(12,2) DEFAULT 0,
            discount NUMERIC(12,2) DEFAULT 0,
            tax NUMERIC(12,2) DEFAULT 0,
            total NUMERIC(12,2) DEFAULT 0,
            payment_method VARCHAR(50),
            payment_detail JSONB DEFAULT '{{}}',
            sync_status VARCHAR(20) DEFAULT 'synced',
            synced_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.transaction_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transaction_id UUID NOT NULL,
            product_id UUID NOT NULL,
            variant_id UUID,
            qty INTEGER NOT NULL,
            unit_price NUMERIC(12,2) NOT NULL,
            discount NUMERIC(12,2) DEFAULT 0,
            subtotal NUMERIC(12,2) NOT NULL
        )
    """))
    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.stock (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID NOT NULL,
            variant_id UUID,
            qty NUMERIC(10,2) DEFAULT 0,
            min_qty NUMERIC(10,2) DEFAULT 5,
            location VARCHAR(100)
        )
    """))
    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.stock_movements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            product_id UUID NOT NULL,
            delta INTEGER NOT NULL,
            type VARCHAR(50) NOT NULL,
            reference_id UUID,
            note VARCHAR(500),
            created_by UUID,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.shifts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cashier_id UUID NOT NULL,
            opening_balance NUMERIC(12,2) DEFAULT 0,
            closing_balance NUMERIC(12,2),
            opened_at TIMESTAMPTZ DEFAULT NOW(),
            closed_at TIMESTAMPTZ,
            status VARCHAR(20) DEFAULT 'open'
        )
    """))
    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.purchase_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            supplier_id UUID,
            status VARCHAR(30) DEFAULT 'draft',
            items JSONB DEFAULT '[]',
            total NUMERIC(12,2) DEFAULT 0,
            received_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
