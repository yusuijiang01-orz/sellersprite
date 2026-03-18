"""
商品 API - 选品列表和详情
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Product, ProductHistory, KeywordProduct

router = APIRouter()


# ============ Request/Response Models ============

class ProductFilter(BaseModel):
    """商品筛选条件"""
    keyword: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_monthly_sales: Optional[int] = None
    max_monthly_sales: Optional[int] = None
    min_review_count: Optional[int] = None
    max_review_count: Optional[int] = None
    min_rating: Optional[float] = None
    is_fba: Optional[bool] = None
    category: Optional[str] = None
    brand: Optional[str] = None


class ProductResponse(BaseModel):
    """商品响应"""
    asin: str
    title: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    price: Optional[float]
    bsr_rank: Optional[int]
    rating: Optional[float]
    review_count: Optional[int]
    monthly_sales: Optional[int]
    monthly_revenue: Optional[float]
    is_fba: bool
    image_url: Optional[str]

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """商品列表响应"""
    total: int
    page: int
    page_size: int
    products: List[ProductResponse]
    filters_applied: dict


class ProductDetailResponse(BaseModel):
    """商品详情响应"""
    asin: str
    title: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    price: Optional[float]
    bsr_rank: Optional[int]
    bsr_category: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    monthly_sales: Optional[int]
    monthly_revenue: Optional[float]
    is_fba: bool
    is_prime: bool
    seller_count: Optional[int]
    image_url: Optional[str]
    description: Optional[str]
    features: Optional[List[str]]
    weight_kg: Optional[float]
    dimensions: Optional[str]

    class Config:
        from_attributes = True


# ============ API Routes ============

@router.get("/products", response_model=ProductListResponse)
async def get_products(
    keyword: Optional[str] = Query(None, description="关联关键词"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_monthly_sales: Optional[int] = Query(None, ge=0),
    max_monthly_sales: Optional[int] = Query(None, ge=0),
    min_review_count: Optional[int] = Query(None, ge=0),
    max_review_count: Optional[int] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    is_fba: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    sort_by: str = Query("monthly_sales", regex="^(monthly_sales|price|rating|review_count|bsr_rank)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    获取选品列表
    
    支持多维度筛选和排序
    """
    # 构建查询
    query = select(Product).distinct()
    
    # 关键词关联
    if keyword:
        query = query.join(KeywordProduct).join(KeywordProduct).where(
            KeywordProduct.position.isnot(None)
        )
    
    # 构建筛选条件
    filters = []
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)
    if min_monthly_sales is not None:
        filters.append(Product.monthly_sales >= min_monthly_sales)
    if max_monthly_sales is not None:
        filters.append(Product.monthly_sales <= max_monthly_sales)
    if min_review_count is not None:
        filters.append(Product.review_count >= min_review_count)
    if max_review_count is not None:
        filters.append(Product.review_count <= max_review_count)
    if min_rating is not None:
        filters.append(Product.rating >= min_rating)
    if is_fba is not None:
        filters.append(Product.is_fba == is_fba)
    if category:
        filters.append(Product.category.ilike(f"%{category}%"))
    if brand:
        filters.append(Product.brand.ilike(f"%{brand}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    # 排序
    sort_column = getattr(Product, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 执行查询
    result = await db.execute(query)
    products = result.scalars().all()
    
    # 转换为响应格式
    product_list = []
    for p in products:
        product_list.append(ProductResponse(
            asin=p.asin,
            title=p.title,
            brand=p.brand,
            category=p.category,
            price=float(p.price) if p.price else None,
            bsr_rank=p.bsr_rank,
            rating=p.rating,
            review_count=p.review_count,
            monthly_sales=p.monthly_sales,
            monthly_revenue=float(p.monthly_revenue) if p.monthly_revenue else None,
            is_fba=p.is_fba,
            image_url=p.image_url
        ))
    
    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        products=product_list,
        filters_applied={
            "keyword": keyword,
            "min_price": min_price,
            "max_price": max_price,
            "min_monthly_sales": min_monthly_sales,
            "max_monthly_sales": max_monthly_sales,
            "min_review_count": min_review_count,
            "max_review_count": max_review_count,
            "min_rating": min_rating,
            "is_fba": is_fba,
            "category": category,
            "brand": brand
        }
    )


@router.get("/products/{asin}", response_model=ProductDetailResponse)
async def get_product_detail(
    asin: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个商品详情
    """
    stmt = select(Product).where(Product.asin == asin.upper())
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ProductDetailResponse(
        asin=product.asin,
        title=product.title,
        brand=product.brand,
        category=product.category,
        price=float(product.price) if product.price else None,
        bsr_rank=product.bsr_rank,
        bsr_category=product.bsr_category,
        rating=product.rating,
        review_count=product.review_count,
        monthly_sales=product.monthly_sales,
        monthly_revenue=float(product.monthly_revenue) if product.monthly_revenue else None,
        is_fba=product.is_fba,
        is_prime=product.is_prime,
        seller_count=product.seller_count,
        image_url=product.image_url,
        description=product.description,
        features=product.features,
        weight_kg=product.weight_kg,
        dimensions=product.dimensions
    )


@router.get("/products/{asin}/history")
async def get_product_history(
    asin: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    获取商品历史趋势
    
    默认返回30天历史数据
    """
    # 检查商品是否存在
    stmt = select(Product).where(Product.asin == asin.upper())
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 获取历史数据
    start_date = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(ProductHistory)
        .where(
            and_(
                ProductHistory.product_id == product.id,
                ProductHistory.recorded_at >= start_date
            )
        )
        .order_by(ProductHistory.recorded_at.asc())
    )
    result = await db.execute(stmt)
    histories = result.scalars().all()
    
    # 转换为时间序列格式
    history_data = []
    for h in histories:
        history_data.append({
            "date": h.recorded_at.isoformat(),
            "price": float(h.price) if h.price else None,
            "bsr_rank": h.bsr_rank,
            "review_count": h.review_count,
            "rating": h.rating,
            "monthly_sales": h.monthly_sales,
            "monthly_revenue": float(h.monthly_revenue) if h.monthly_revenue else None
        })
    
    return {
        "asin": asin.upper(),
        "product_name": product.title,
        "days": days,
        "history": history_data
    }
