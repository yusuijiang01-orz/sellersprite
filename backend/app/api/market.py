"""
市场 API - 市场概览和竞争分析
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models import Product, KeywordProduct, Keyword, MarketOverview

router = APIRouter()


# ============ Response Models ============

class MarketOverviewResponse(BaseModel):
    """市场概览响应"""
    keyword: str
    total_products: int
    total_monthly_sales: int
    total_monthly_revenue: float
    avg_price: float
    min_price: float
    max_price: float
    avg_review_count: float
    avg_rating: float
    top_10_concentration: float
    price_distribution: dict
    brand_distribution: dict


class CategoryAnalysisResponse(BaseModel):
    """类目分析响应"""
    category: str
    product_count: int
    avg_price: float
    avg_monthly_sales: float
    avg_review_count: float
    competition_score: float


class BrandAnalysisResponse(BaseModel):
    """品牌分析响应"""
    brand: str
    product_count: int
    avg_price: float
    avg_rating: float
    total_monthly_sales: int
    market_share: float


# ============ API Routes ============

@router.get("/market/overview")
async def get_market_overview(
    keyword: str = Query(..., description="关键词"),
    marketplace: str = Query("US", description="市场"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取市场概览
    
    返回关键词对应的市场竞争情况
    """
    # 尝试从缓存表获取
    stmt = select(MarketOverview).where(
        MarketOverview.keyword == keyword.lower(),
        MarketOverview.marketplace == marketplace
    )
    result = await db.execute(stmt)
    cached = result.scalar_one_or_none()
    
    if cached:
        return MarketOverviewResponse(
            keyword=cached.keyword,
            total_products=cached.total_products,
            total_monthly_sales=cached.total_monthly_sales,
            total_monthly_revenue=float(cached.total_monthly_revenue) or 0,
            avg_price=float(cached.avg_price) or 0,
            min_price=float(cached.min_price) or 0,
            max_price=float(cached.max_price) or 0,
            avg_review_count=cached.avg_review_count or 0,
            avg_rating=cached.avg_rating or 0,
            top_10_concentration=cached.top_10_concentration or 0,
            price_distribution=cached.price_distribution or {},
            brand_distribution=cached.brand_distribution or {}
        )
    
    # 如果没有缓存，实时计算
    # 获取关键词关联的商品
    stmt = (
        select(KeywordProduct)
        .join(Keyword)
        .join(Product)
        .where(
            Keyword.keyword == keyword.lower(),
            Keyword.marketplace == marketplace
        )
    )
    result = await db.execute(stmt)
    keyword_products = result.scalars().all()
    
    if not keyword_products:
        raise HTTPException(
            status_code=404,
            detail=f"关键词 '{keyword}' 暂无数据，请先进行搜索"
        )
    
    # 加载商品数据
    product_ids = [kp.product_id for kp in keyword_products]
    stmt = select(Product).where(Product.id.in_(product_ids))
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    # 计算市场指标
    total = len(products)
    prices = [p.price for p in products if p.price]
    review_counts = [p.review_count for p in products if p.review_count]
    ratings = [p.rating for p in products if p.rating]
    monthly_sales = [p.monthly_sales for p in products if p.monthly_sales]
    monthly_revenues = [p.monthly_revenue for p in products if p.monthly_revenue]
    
    # 按品牌统计
    brand_stats = {}
    for p in products:
        if p.brand:
            if p.brand not in brand_stats:
                brand_stats[p.brand] = {"count": 0, "sales": 0}
            brand_stats[p.brand]["count"] += 1
            brand_stats[p.brand]["sales"] += p.monthly_sales or 0
    
    # 计算品牌集中度（Top 10 占比）
    total_sales = sum(s["sales"] for s in brand_stats.values())
    sorted_brands = sorted(brand_stats.items(), key=lambda x: x[1]["sales"], reverse=True)
    top_10_sales = sum(s[1]["sales"] for s in sorted_brands[:10])
    top_10_concentration = (top_10_sales / total_sales * 100) if total_sales > 0 else 0
    
    # 价格分布
    price_distribution = {
        "0-10": 0,
        "10-20": 0,
        "20-50": 0,
        "50-100": 0,
        "100+": 0
    }
    for p in prices:
        if p < 10:
            price_distribution["0-10"] += 1
        elif p < 20:
            price_distribution["10-20"] += 1
        elif p < 50:
            price_distribution["20-50"] += 1
        elif p < 100:
            price_distribution["50-100"] += 1
        else:
            price_distribution["100+"] += 1
    
    # 转换为百分比
    for k in price_distribution:
        price_distribution[k] = round(price_distribution[k] / total * 100, 1) if total > 0 else 0
    
    overview = MarketOverviewResponse(
        keyword=keyword.lower(),
        total_products=total,
        total_monthly_sales=sum(monthly_sales),
        total_monthly_revenue=float(sum(monthly_revenues)),
        avg_price=sum(prices) / len(prices) if prices else 0,
        min_price=min(prices) if prices else 0,
        max_price=max(prices) if prices else 0,
        avg_review_count=sum(review_counts) / len(review_counts) if review_counts else 0,
        avg_rating=sum(ratings) / len(ratings) if ratings else 0,
        top_10_concentration=round(top_10_concentration, 1),
        price_distribution=price_distribution,
        brand_distribution={k: {"count": v["count"], "sales": v["sales"]} for k, v in sorted_brands[:10]}
    )
    
    return overview


@router.get("/market/categories", response_model=List[CategoryAnalysisResponse])
async def get_category_analysis(
    keyword: str = Query(..., description="关键词"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    获取类目分析
    
    返回相关类目的竞争情况
    """
    # 获取关键词关联的商品
    stmt = (
        select(Product.category, func.count(Product.id).label("count"))
        .join(KeywordProduct)
        .join(Keyword)
        .where(Keyword.keyword == keyword.lower())
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    categories = result.all()
    
    category_list = []
    for cat, count in categories:
        if not cat:
            continue
        
        # 获取该类目下的商品统计
        stmt = select(Product).where(Product.category == cat)
        result = await db.execute(stmt)
        cat_products = result.scalars().all()
        
        prices = [p.price for p in cat_products if p.price]
        sales = [p.monthly_sales for p in cat_products if p.monthly_sales]
        reviews = [p.review_count for p in cat_products if p.review_count]
        
        # 计算竞争得分（评论数越多竞争越激烈）
        avg_reviews = sum(reviews) / len(reviews) if reviews else 0
        competition_score = min(avg_reviews / 500, 1.0) * 100  # 归一化到0-100
        
        category_list.append(CategoryAnalysisResponse(
            category=cat,
            product_count=count,
            avg_price=sum(prices) / len(prices) if prices else 0,
            avg_monthly_sales=sum(sales) / len(sales) if sales else 0,
            avg_review_count=avg_reviews,
            competition_score=round(competition_score, 1)
        ))
    
    return category_list


@router.get("/market/brands", response_model=List[BrandAnalysisResponse])
async def get_brand_analysis(
    keyword: str = Query(..., description="关键词"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    获取品牌分析
    
    返回主要品牌的竞争情况
    """
    stmt = (
        select(
            Product.brand,
            func.count(Product.id).label("count"),
            func.avg(Product.price).label("avg_price"),
            func.avg(Product.rating).label("avg_rating"),
            func.sum(Product.monthly_sales).label("total_sales")
        )
        .join(KeywordProduct)
        .join(Keyword)
        .where(
            Keyword.keyword == keyword.lower(),
            Product.brand.isnot(None)
        )
        .group_by(Product.brand)
        .order_by(func.sum(Product.monthly_sales).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    brands = result.all()
    
    # 计算总销量
    total_sales = sum(b.total_sales or 0 for b in brands)
    
    brand_list = []
    for b in brands:
        if not b.brand:
            continue
        
        market_share = (b.total_sales / total_sales * 100) if total_sales > 0 else 0
        
        brand_list.append(BrandAnalysisResponse(
            brand=b.brand,
            product_count=b.count,
            avg_price=float(b.avg_price) if b.avg_price else 0,
            avg_rating=float(b.avg_rating) if b.avg_rating else 0,
            total_monthly_sales=b.total_sales or 0,
            market_share=round(market_share, 1)
        ))
    
    return brand_list
