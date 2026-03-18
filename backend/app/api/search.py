"""
搜索 API - 关键词搜索入口
触发爬虫任务，返回任务状态
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
import json

from app.database import get_db
from app.models import Keyword, ScrapeTask, MarketOverview
from app.config import settings
from app.tasks import scrape_keyword  # Celery 任务

router = APIRouter()


# ============ Request/Response Models ============

class SearchRequest(BaseModel):
    """搜索请求"""
    keyword: str
    marketplace: str = "US"
    pages: int = 3


class SearchResponse(BaseModel):
    """搜索响应"""
    task_id: str
    status: str
    message: str
    keyword: str


class SearchResultResponse(BaseModel):
    """搜索结果响应"""
    keyword: str
    total_results: int
    products: list
    market_overview: Optional[dict] = None


# ============ API Routes ============

@router.post("/search", response_model=SearchResponse)
async def create_search_task(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    关键词搜索入口
    
    1. 检查缓存
    2. 检查是否有进行中的任务
    3. 创建 Celery 异步任务
    4. 返回任务ID供前端轮询
    """
    keyword = request.keyword.strip().lower()
    
    # 1. 检查缓存
    cache_key = f"{settings.cache_search_prefix}{keyword}:{request.marketplace}"
    # TODO: 从 Redis 获取缓存
    
    # 2. 检查数据库是否有进行中的任务
    stmt = select(ScrapeTask).where(
        and_(
            ScrapeTask.keyword == keyword,
            ScrapeTask.marketplace == request.marketplace,
            ScrapeTask.status.in_(["pending", "running"])
        )
    )
    result = await db.execute(stmt)
    existing_task = result.scalar_one_or_none()
    
    if existing_task:
        return SearchResponse(
            task_id=existing_task.task_id or str(existing_task.id),
            status=existing_task.status,
            message="该关键词已有进行中的任务，请稍候查询",
            keyword=keyword
        )
    
    # 3. 创建爬虫任务记录
    new_task = ScrapeTask(
        keyword=keyword,
        marketplace=request.marketplace,
        pages=request.pages,
        status="pending"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # 4. 触发 Celery 异步任务
    try:
        celery_task = scrape_keyword.delay(
            keyword=keyword,
            marketplace=request.marketplace,
            pages=request.pages,
            task_id=str(new_task.id)
        )
        
        # 更新任务 ID
        new_task.task_id = celery_task.id
        await db.commit()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动爬虫任务失败: {str(e)}")
    
    return SearchResponse(
        task_id=str(new_task.id),
        status="pending",
        message="数据采集中，请稍候查询结果",
        keyword=keyword
    )


@router.get("/search/{task_id}")
async def get_search_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询爬虫任务状态
    
    返回状态：pending / running / done / failed
    如果完成，返回商品数据
    """
    stmt = select(ScrapeTask).where(ScrapeTask.id == int(task_id))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result_count": task.result_count,
        "error_msg": task.error_msg,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None
    }


@router.get("/search/{task_id}/results", response_model=SearchResultResponse)
async def get_search_results(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取搜索结果
    
    仅在任务完成后调用
    """
    # 1. 获取任务状态
    stmt = select(ScrapeTask).where(ScrapeTask.id == int(task_id))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != "done":
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task.status}")
    
    # 2. 获取关键词ID
    stmt = select(Keyword).where(Keyword.keyword == task.keyword)
    result = await db.execute(stmt)
    keyword_obj = result.scalar_one_or_none()
    
    if not keyword_obj:
        raise HTTPException(status_code=404, detail="关键词数据不存在")
    
    # 3. 获取关联商品
    from sqlalchemy.orm import selectinload
    stmt = (
        select(KeywordProduct)
        .options(selectinload(KeywordProduct.product))
        .where(KeywordProduct.keyword_id == keyword_obj.id)
        .order_by(KeywordProduct.position)
    )
    result = await db.execute(stmt)
    keyword_products = result.scalars().all()
    
    products = []
    for kp in keyword_products:
        p = kp.product
        products.append({
            "asin": p.asin,
            "title": p.title,
            "brand": p.brand,
            "price": float(p.price) if p.price else None,
            "bsr_rank": p.bsr_rank,
            "rating": p.rating,
            "review_count": p.review_count,
            "monthly_sales": p.monthly_sales,
            "monthly_revenue": float(p.monthly_revenue) if p.monthly_revenue else None,
            "is_fba": p.is_fba,
            "image_url": p.image_url,
            "position": kp.position
        })
    
    # 4. 获取市场概览
    stmt = select(MarketOverview).where(
        MarketOverview.keyword == task.keyword
    )
    result = await db.execute(stmt)
    market = result.scalar_one_or_none()
    
    market_overview = None
    if market:
        market_overview = {
            "total_products": market.total_products,
            "total_monthly_sales": market.total_monthly_sales,
            "total_monthly_revenue": float(market.total_monthly_revenue) if market.total_monthly_revenue else None,
            "avg_price": float(market.avg_price) if market.avg_price else None,
            "avg_review_count": market.avg_review_count,
            "avg_rating": market.avg_rating
        }
    
    return SearchResultResponse(
        keyword=task.keyword,
        total_results=len(products),
        products=products,
        market_overview=market_overview
    )
