import os
import csv
import uuid
from app.workers.celery_app import celery_app

EXPORT_DIR = "/tmp/kasirpro_exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


@celery_app.task(name="report.generate_export", bind=True, max_retries=3)
def generate_report_export(self, report_type: str, format: str, branch_schema: str,
                           date_from=None, date_to=None):
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import text
    from app.core.config import settings

    async def _run():
        engine = create_async_engine(settings.DATABASE_URL)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        async with SessionLocal() as db:
            where = ""
            params = {}
            if date_from:
                where += " AND created_at >= :date_from"
                params["date_from"] = date_from
            if date_to:
                where += " AND created_at <= :date_to"
                params["date_to"] = date_to

            if report_type == "sales":
                result = await db.execute(text(f"""
                    SELECT invoice_no, total, payment_method, sync_status, created_at
                    FROM {branch_schema}.transactions
                    WHERE sync_status != 'void' {where}
                    ORDER BY created_at DESC
                """), params)
                rows = result.mappings().all()
                headers = ["invoice_no", "total", "payment_method", "sync_status", "created_at"]
            elif report_type == "stock":
                result = await db.execute(text(f"""
                    SELECT s.product_id, p.name, p.sku,
                           s.qty + COALESCE(SUM(sm.delta), 0) AS current_qty, s.min_qty
                    FROM {branch_schema}.stock s
                    LEFT JOIN {branch_schema}.stock_movements sm ON sm.product_id = s.product_id
                    JOIN public.products p ON p.id = s.product_id
                    GROUP BY s.product_id, p.name, p.sku, s.qty, s.min_qty
                """), {})
                rows = result.mappings().all()
                headers = ["product_id", "name", "sku", "current_qty", "min_qty"]
            else:
                rows, headers = [], []

        await engine.dispose()
        return rows, headers

    rows, headers = asyncio.run(_run())

    file_id = str(uuid.uuid4())[:8]
    filename = f"{report_type}_{file_id}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: v.isoformat() if hasattr(v, "isoformat") else str(v) if v is not None else ""
                for k, v in dict(row).items()
                if k in headers
            })

    return filepath
