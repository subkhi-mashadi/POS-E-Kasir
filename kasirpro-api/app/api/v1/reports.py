from fastapi import APIRouter, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from uuid import UUID
import os
from app.core.database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales")
async def sales_report(
    branch_schema: str = "public",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    group_by: str = "day",  # day | week | month
    db: AsyncSession = Depends(get_db),
):
    date_trunc = {"day": "day", "week": "week", "month": "month"}.get(group_by, "day")
    where = _build_date_where(date_from, date_to)
    params = _build_date_params(date_from, date_to)

    result = await db.execute(text(f"""
        SELECT
            DATE_TRUNC('{date_trunc}', created_at) AS period,
            COUNT(*) AS transaction_count,
            SUM(total) AS total_sales,
            SUM(discount) AS total_discount,
            SUM(tax) AS total_tax,
            AVG(total) AS avg_transaction
        FROM {branch_schema}.transactions
        WHERE sync_status != 'void' {where}
        GROUP BY DATE_TRUNC('{date_trunc}', created_at)
        ORDER BY period DESC
    """), params)

    rows = result.mappings().all()
    return [_serialize_row(r) for r in rows]


@router.get("/products")
async def products_report(
    branch_schema: str = "public",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20,
    order: str = "desc",  # desc=terlaris, asc=terlamban
    db: AsyncSession = Depends(get_db),
):
    where = _build_date_where(date_from, date_to, prefix="t.")
    params = _build_date_params(date_from, date_to)
    params["limit"] = limit

    result = await db.execute(text(f"""
        SELECT
            ti.product_id,
            p.name AS product_name,
            p.sku,
            SUM(ti.qty) AS total_qty_sold,
            SUM(ti.subtotal) AS total_revenue,
            COUNT(DISTINCT ti.transaction_id) AS transaction_count
        FROM {branch_schema}.transaction_items ti
        JOIN {branch_schema}.transactions t ON t.id = ti.transaction_id
        JOIN public.products p ON p.id = ti.product_id
        WHERE t.sync_status != 'void' {where}
        GROUP BY ti.product_id, p.name, p.sku
        ORDER BY total_qty_sold {'DESC' if order == 'desc' else 'ASC'}
        LIMIT :limit
    """), params)

    return [_serialize_row(r) for r in result.mappings().all()]


@router.get("/cashier")
async def cashier_report(
    branch_schema: str = "public",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    where = _build_date_where(date_from, date_to)
    params = _build_date_params(date_from, date_to)

    result = await db.execute(text(f"""
        SELECT
            t.cashier_id,
            u.name AS cashier_name,
            COUNT(*) AS transaction_count,
            SUM(t.total) AS total_sales,
            AVG(t.total) AS avg_transaction,
            MIN(t.created_at) AS first_transaction,
            MAX(t.created_at) AS last_transaction
        FROM {branch_schema}.transactions t
        LEFT JOIN public.users u ON u.id = t.cashier_id
        WHERE t.sync_status != 'void' {where}
        GROUP BY t.cashier_id, u.name
        ORDER BY total_sales DESC
    """), params)

    return [_serialize_row(r) for r in result.mappings().all()]


@router.get("/stock")
async def stock_report(branch_schema: str = "public", db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(f"""
        SELECT
            s.product_id,
            p.name AS product_name,
            p.sku,
            p.cost_price,
            s.qty + COALESCE(SUM(sm.delta), 0) AS current_qty,
            s.min_qty,
            p.cost_price * (s.qty + COALESCE(SUM(sm.delta), 0)) AS stock_value,
            CASE WHEN s.qty + COALESCE(SUM(sm.delta), 0) <= s.min_qty THEN true ELSE false END AS is_low
        FROM {branch_schema}.stock s
        LEFT JOIN {branch_schema}.stock_movements sm ON sm.product_id = s.product_id
        JOIN public.products p ON p.id = s.product_id
        GROUP BY s.product_id, p.name, p.sku, p.cost_price, s.qty, s.min_qty
        ORDER BY is_low DESC, current_qty ASC
    """))

    return [_serialize_row(r) for r in result.mappings().all()]


@router.get("/consolidated")
async def consolidated_report(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.models.public.branch import Branch
    from sqlalchemy import select
    branches_result = await db.execute(select(Branch).where(Branch.is_active == True))
    branches = branches_result.scalars().all()

    where = _build_date_where(date_from, date_to)
    params = _build_date_params(date_from, date_to)

    consolidated = []
    grand_total = 0.0
    for branch in branches:
        try:
            r = await db.execute(text(f"""
                SELECT
                    COUNT(*) AS transaction_count,
                    COALESCE(SUM(total), 0) AS total_sales,
                    COALESCE(SUM(discount), 0) AS total_discount
                FROM {branch.schema_name}.transactions
                WHERE sync_status != 'void' {where}
            """), params)
            row = r.mappings().one()
            sales = float(row["total_sales"])
            grand_total += sales
            consolidated.append({
                "branch_id": str(branch.id),
                "branch_name": branch.name,
                "transaction_count": int(row["transaction_count"]),
                "total_sales": sales,
                "total_discount": float(row["total_discount"]),
            })
        except Exception:
            consolidated.append({
                "branch_id": str(branch.id),
                "branch_name": branch.name,
                "transaction_count": 0,
                "total_sales": 0.0,
                "total_discount": 0.0,
            })

    return {"branches": consolidated, "grand_total": grand_total, "date_from": date_from, "date_to": date_to}


@router.get("/export")
async def export_report(
    background_tasks: BackgroundTasks,
    report_type: str = "sales",
    format: str = "csv",  # csv | excel (excel requires openpyxl)
    branch_schema: str = "public",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    from app.workers.report_worker import generate_report_export
    task = generate_report_export.delay(report_type, format, branch_schema, date_from, date_to)
    return {"task_id": task.id, "status": "queued", "message": "Laporan sedang dibuat"}


@router.get("/export/{task_id}/download")
async def download_report(task_id: str):
    from app.workers.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)
    if result.state == "SUCCESS":
        file_path = result.get()
        if os.path.exists(file_path):
            return FileResponse(file_path, filename=os.path.basename(file_path))
    return {"status": result.state, "ready": result.ready()}


def _build_date_where(date_from, date_to, prefix="") -> str:
    parts = []
    if date_from:
        parts.append(f"AND {prefix}created_at >= :date_from")
    if date_to:
        parts.append(f"AND {prefix}created_at <= :date_to")
    return " ".join(parts)


def _build_date_params(date_from, date_to) -> dict:
    p = {}
    if date_from:
        p["date_from"] = date_from
    if date_to:
        p["date_to"] = date_to
    return p


def _serialize_row(row) -> dict:
    result = {}
    for k, v in dict(row).items():
        if hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        elif hasattr(v, "__float__"):
            result[k] = float(v)
        else:
            result[k] = v
    return result
