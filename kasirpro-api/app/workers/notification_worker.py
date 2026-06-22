import asyncio
import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="notification.check_low_stock")
def check_low_stock_and_notify(branch_schema: str, branch_name: str):
    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import text
        from app.core.config import settings
        from app.services.notification_service import send_low_stock_alert

        engine = create_async_engine(settings.DATABASE_URL)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

        async with SessionLocal() as db:
            result = await db.execute(text(f"""
                SELECT p.name, p.sku,
                       s.qty + COALESCE(SUM(sm.delta), 0) AS current_qty,
                       s.min_qty
                FROM {branch_schema}.stock s
                LEFT JOIN {branch_schema}.stock_movements sm
                    ON sm.product_id = s.product_id
                JOIN public.products p ON p.id = s.product_id
                GROUP BY p.name, p.sku, s.qty, s.min_qty
                HAVING s.qty + COALESCE(SUM(sm.delta), 0) <= s.min_qty
            """))
            low_items = [dict(r._mapping) for r in result]

        await engine.dispose()

        if low_items:
            await send_low_stock_alert(branch_name, low_items)
            logger.info("[LOW STOCK] %d items di %s", len(low_items), branch_name)

        return {"notified": len(low_items), "branch": branch_name}

    return asyncio.run(_run())


@celery_app.task(name="notification.daily_report")
def send_daily_report():
    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy import select, text
        from app.core.config import settings
        from app.models.public.branch import Branch
        from app.services.notification_service import send_daily_report_telegram

        engine = create_async_engine(settings.DATABASE_URL)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

        async with SessionLocal() as db:
            branches_result = await db.execute(
                select(Branch).where(Branch.is_active == True)
            )
            branches = branches_result.scalars().all()
            summary = []
            grand_total = 0.0

            for branch in branches:
                try:
                    r = await db.execute(text(f"""
                        SELECT COALESCE(SUM(total), 0) AS sales, COUNT(*) AS count
                        FROM {branch.schema_name}.transactions
                        WHERE DATE(created_at) = CURRENT_DATE
                          AND sync_status != 'void'
                    """))
                    row = r.mappings().one()
                    sales = float(row["sales"])
                    grand_total += sales
                    summary.append({
                        "branch": branch.name,
                        "sales": sales,
                        "count": int(row["count"]),
                    })
                except Exception:
                    pass

        await engine.dispose()
        await send_daily_report_telegram(summary, grand_total)
        logger.info("[DAILY REPORT] sent, total=%.2f", grand_total)
        return {"summary": summary, "grand_total": grand_total}

    return asyncio.run(_run())
