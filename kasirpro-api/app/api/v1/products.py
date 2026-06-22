from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.models.public.product import Product, Category
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryResponse, PaginatedProducts
)

router = APIRouter(prefix="/products", tags=["products"])

@router.get("", response_model=PaginatedProducts)
async def list_products(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db)
):
    q = select(Product)
    if search:
        q = q.where(or_(
            Product.name.ilike(f"%{search}%"),
            Product.sku.ilike(f"%{search}%"),
            Product.barcode == search
        ))
    if category_id:
        q = q.where(Product.category_id == category_id)
    if is_active is not None:
        q = q.where(Product.is_active == is_active)

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar()

    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    products = result.scalars().all()

    return PaginatedProducts(items=products, total=total, page=page, per_page=per_page)

@router.get("/sync")
async def sync_products(since: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    q = select(Product).where(Product.is_active == True)
    if since:
        ts = datetime.fromisoformat(since)
        q = q.where(Product.updated_at >= ts)
    result = await db.execute(q)
    return result.scalars().all()

@router.get("/barcode/{code}", response_model=ProductResponse)
async def get_by_barcode(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.barcode == code))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Product not found")
    return product

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Product not found")
    return product

@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Product not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    from datetime import datetime, timezone
    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Product not found")
    product.is_active = False
    await db.commit()

# Categories
@router.get("/categories/all", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.sort_order))
    return result.scalars().all()

@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    cat = Category(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat
