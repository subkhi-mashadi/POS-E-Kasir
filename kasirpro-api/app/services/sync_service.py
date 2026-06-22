from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


async def resolve_transaction_conflict(
    db: AsyncSession,
    schema: str,
    local_id: UUID,
) -> str:
    """
    Check if transaction with local_id already exists.
    Returns: 'exists' | 'not_found'
    Idempotent: duplicate sync is safe because local_id is UNIQUE.
    """
    result = await db.execute(
        text(f"SELECT id FROM {schema}.transactions WHERE local_id = :lid"),
        {"lid": str(local_id)},
    )
    return "exists" if result.scalar_one_or_none() else "not_found"


async def apply_stock_deltas(
    db: AsyncSession,
    schema: str,
    deltas: List[dict],
    reference_id: str,
) -> None:
    """
    Apply list of stock deltas. Delta-based = no conflict: each movement
    is additive. Two offline cashiers selling the same product both get
    recorded; server sums all deltas for actual stock level.
    """
    for delta in deltas:
        await db.execute(
            text(f"""
                INSERT INTO {schema}.stock_movements
                (id, product_id, delta, type, reference_id, created_at)
                VALUES (gen_random_uuid(), :pid, :delta, :type, :ref, NOW())
            """),
            {
                "pid": str(delta["product_id"]),
                "delta": delta["delta"],
                "type": delta.get("type", "sale"),
                "ref": reference_id,
            },
        )
    logger.info("Applied %d stock deltas for ref %s", len(deltas), reference_id)
