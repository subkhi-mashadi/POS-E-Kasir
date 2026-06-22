from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.models.public.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["customers"])

POINTS_PER_RUPIAH = 1 / 10000  # 1 poin per Rp 10.000


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db)
):
    q = select(Customer)
    if search:
        q = q.where(or_(
            Customer.name.ilike(f"%{search}%"),
            Customer.phone.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%"),
        ))
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    customer = Customer(**data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: UUID, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "Customer not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(customer, k, v)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.post("/{customer_id}/points")
async def adjust_points(
    customer_id: UUID,
    delta: int,
    reason: str = "manual",
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "Customer not found")
    customer.points = max(0, (customer.points or 0) + delta)
    customer.tier = _calculate_tier(customer.points)
    await db.commit()
    return {"points": customer.points, "tier": customer.tier}


@router.post("/{customer_id}/points/earn")
async def earn_points(customer_id: UUID, transaction_total: float, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(404, "Customer not found")
    earned = int(transaction_total * POINTS_PER_RUPIAH)
    customer.points = (customer.points or 0) + earned
    customer.tier = _calculate_tier(customer.points)
    await db.commit()
    return {"earned": earned, "total_points": customer.points, "tier": customer.tier}


def _calculate_tier(points: int) -> str:
    if points >= 10000:
        return "platinum"
    if points >= 5000:
        return "gold"
    if points >= 1000:
        return "silver"
    return "bronze"
