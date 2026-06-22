from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.public.promotion import Promotion
from app.schemas.promotion import PromotionCreate, PromotionResponse, ApplyPromotionRequest

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get("", response_model=list[PromotionResponse])
async def list_promotions(active_only: bool = True, db: AsyncSession = Depends(get_db)):
    q = select(Promotion)
    if active_only:
        now = datetime.now(timezone.utc)
        q = q.where(Promotion.start_at <= now, Promotion.end_at >= now)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=PromotionResponse, status_code=201)
async def create_promotion(data: PromotionCreate, db: AsyncSession = Depends(get_db)):
    promo = Promotion(**data.model_dump())
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return promo


@router.post("/apply")
async def apply_promotion(data: ApplyPromotionRequest, db: AsyncSession = Depends(get_db)):
    """Calculate discount for a cart given active promotions."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Promotion).where(Promotion.start_at <= now, Promotion.end_at >= now)
    )
    promotions = result.scalars().all()

    total_discount = 0.0
    applied = []

    for promo in promotions:
        conditions = promo.conditions or {}

        if promo.type == "percentage":
            min_purchase = conditions.get("min_purchase", 0)
            if data.subtotal >= min_purchase:
                discount = data.subtotal * (float(promo.discount_value) / 100)
                total_discount += discount
                applied.append({"name": promo.name, "discount": discount})

        elif promo.type == "fixed":
            min_purchase = conditions.get("min_purchase", 0)
            if data.subtotal >= min_purchase:
                discount = float(promo.discount_value)
                total_discount += discount
                applied.append({"name": promo.name, "discount": discount})

        elif promo.type == "buy_x_get_y":
            buy_qty = conditions.get("buy_qty", 1)
            get_qty = conditions.get("get_qty", 1)
            product_id = conditions.get("product_id")
            item = next((i for i in data.items if i.get("product_id") == product_id), None)
            if item and item.get("qty", 0) >= buy_qty:
                free_qty = (item["qty"] // buy_qty) * get_qty
                discount = free_qty * item.get("unit_price", 0)
                total_discount += discount
                applied.append({"name": promo.name, "discount": discount, "free_qty": free_qty})

    return {
        "total_discount": round(total_discount, 2),
        "applied_promotions": applied,
        "final_subtotal": max(0, data.subtotal - total_discount),
    }


@router.delete("/{promo_id}", status_code=204)
async def delete_promotion(promo_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Promotion).where(Promotion.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(404, "Promotion not found")
    await db.delete(promo)
    await db.commit()
