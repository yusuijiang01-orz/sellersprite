"""
Celery 任务 - 爬虫逻辑
使用 Playwright 爬取亚马逊搜索结果
"""
import asyncio
import random
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.celery_app import celery_app
from app.config import settings
from app.models import (
    Keyword, Product, KeywordProduct, ScrapeTask, MarketOverview,
    ProductHistory
)
from app.scraper import AmazonScraper


# 创建独立的数据库会话（用于 Celery 任务）
engine = create_async_engine(settings.database_url_async, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_task_db():
    """获取任务数据库会话"""
    async with async_session_maker() as session:
        yield session


@celery_app.task(bind=True, max_retries=3)
def scrape_keyword(self, keyword: str, marketplace: str = "US", pages: int = 3, task_id: int = None):
    """
    爬取关键词搜索结果
    
    异步任务，由 Celery Worker 执行
    """
    asyncio.run(_scrape_keyword_async(keyword, marketplace, pages, task_id))


async def _scrape_keyword_async(keyword: str, marketplace: str, pages: int, task_id: int):
    """爬取关键词的实际异步逻辑"""
    
    async with async_session_maker() as db:
        try:
            # 1. 更新任务状态为 running
            if task_id:
                stmt = select(ScrapeTask).where(ScrapeTask.id == int(task_id))
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if task:
                    task.status = "running"
                    await db.commit()
            
            # 2. 初始化爬虫
            scraper = AmazonScraper()
            
            # 3. 爬取数据
            products_data = await scraper.scrape_search_results(
                keyword=keyword,
                pages=pages,
                marketplace=marketplace
            )
            
            # 4. 保存到数据库
            keyword_obj = None
            
            for idx, product_data in enumerate(products_data):
                # 保存/更新商品
                stmt = select(Product).where(Product.asin == product_data["asin"])
                result = await db.execute(stmt)
                product = result.scalar_one_or_none()
                
                if product:
                    # 更新现有商品
                    product.title = product_data.get("title")
                    product.price = product_data.get("price")
                    product.rating = product_data.get("rating")
                    product.review_count = product_data.get("review_count")
                    product.bsr_rank = product_data.get("bsr_rank")
                    product.monthly_sales = product_data.get("monthly_sales")
                    product.monthly_revenue = product_data.get("monthly_revenue")
                    product.is_fba = product_data.get("is_fba", False)
                    product.image_url = product_data.get("image_url")
                    product.last_updated = datetime.utcnow()
                else:
                    # 创建新商品
                    product = Product(
                        asin=product_data["asin"],
                        title=product_data.get("title"),
                        price=product_data.get("price"),
                        rating=product_data.get("rating"),
                        review_count=product_data.get("review_count"),
                        bsr_rank=product_data.get("bsr_rank"),
                        monthly_sales=product_data.get("monthly_sales"),
                        monthly_revenue=product_data.get("monthly_revenue"),
                        is_fba=product_data.get("is_fba", False),
                        image_url=product_data.get("image_url"),
                        category=product_data.get("category"),
                        brand=product_data.get("brand"),
                        detail_url=product_data.get("detail_url")
                    )
                    db.add(product)
                
                await db.flush()
                
                # 保存关键词关联
                if idx == 0 and not keyword_obj:
                    # 创建或获取关键词
                    stmt = select(Keyword).where(
                        and_(
                            Keyword.keyword == keyword.lower(),
                            Keyword.marketplace == marketplace
                        )
                    )
                    result = await db.execute(stmt)
                    keyword_obj = result.scalar_one_or_none()
                    
                    if not keyword_obj:
                        keyword_obj = Keyword(
                            keyword=keyword.lower(),
                            marketplace=marketplace,
                            search_volume=sum(p.get("monthly_sales", 0) for p in products_data)
                        )
                        db.add(keyword_obj)
                        await db.flush()
                
                # 关联关键词和商品
                stmt = select(KeywordProduct).where(
                    and_(
                        KeywordProduct.keyword_id == keyword_obj.id,
                        KeywordProduct.product_id == product.id
                    )
                )
                result = await db.execute(stmt)
                kp = result.scalar_one_or_none()
                
                if not kp:
                    kp = KeywordProduct(
                        keyword_id=keyword_obj.id,
                        product_id=product.id,
                        position=idx + 1,
                        page=(idx // 48) + 1  # 假设每页48个
                    )
                    db.add(kp)
            
            # 5. 记录商品历史
            for product_data in products_data[:10]:  # 只记录前10个
                stmt = select(Product).where(Product.asin == product_data["asin"])
                result = await db.execute(stmt)
                product = result.scalar_one_or_none()
                
                if product:
                    history = ProductHistory(
                        product_id=product.id,
                        price=product_data.get("price"),
                        bsr_rank=product_data.get("bsr_rank"),
                        review_count=product_data.get("review_count"),
                        monthly_sales=product_data.get("monthly_sales"),
                        monthly_revenue=product_data.get("monthly_revenue"),
                        is_fba=product_data.get("is_fba", False)
                    )
                    db.add(history)
            
            # 6. 更新任务状态
            if task_id:
                stmt = select(ScrapeTask).where(ScrapeTask.id == int(task_id))
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if task:
                    task.status = "done"
                    task.result_count = len(products_data)
                    task.finished_at = datetime.utcnow()
            
            # 7. 计算市场概览
            await calculate_market_for_keyword(db, keyword.lower(), marketplace)
            
            await db.commit()
            print(f"✅ 爬取完成: {keyword}, 获取 {len(products_data)} 个商品")
            
        except Exception as e:
            print(f"❌ 爬取失败: {keyword}, 错误: {str(e)}")
            
            # 更新任务状态为失败
            if task_id:
                stmt = select(ScrapeTask).where(ScrapeTask.id == int(task_id))
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_msg = str(e)
                    task.finished_at = datetime.utcnow()
                    await db.commit()
            
            # 重试
            raise self.retry(exc=e, countdown=60)


async def calculate_market_for_keyword(db: AsyncSession, keyword: str, marketplace: str):
    """计算市场概览数据"""
    
    # 获取关键词关联的所有商品
    stmt = (
        select(KeywordProduct)
        .join(Keyword)
        .where(
            Keyword.keyword == keyword,
            Keyword.marketplace == marketplace
        )
    )
    result = await db.execute(stmt)
    keyword_products = result.scalars().all()
    
    if not keyword_products:
        return
    
    # 获取商品详情
    product_ids = [kp.product_id for kp in keyword_products]
    stmt = select(Product).where(Product.id.in_(product_ids))
    result = await db.execute(stmt)
    products = result.scalars().all()
    
    if not products:
        return
    
    # 计算统计数据
    total = len(products)
    prices = [p.price for p in products if p.price]
    sales = [p.monthly_sales for p in products if p.monthly_sales]
    revenues = [p.monthly_revenue for p in products if p.monthly_revenue]
    reviews = [p.review_count for p in products if p.review_count]
    ratings = [p.rating for p in products if p.rating]
    
    # 保存市场概览
    overview = MarketOverview(
        keyword=keyword,
        marketplace=marketplace,
        total_products=total,
        total_monthly_sales=sum(sales) if sales else 0,
        total_monthly_revenue=sum(revenues) if revenues else 0,
        avg_price=sum(prices) / len(prices) if prices else 0,
        min_price=min(prices) if prices else 0,
        max_price=max(prices) if prices else 0,
        avg_review_count=sum(reviews) / len(reviews) if reviews else 0,
        avg_rating=sum(ratings) / len(ratings) if ratings else 0
    )
    
    # 检查是否已存在
    stmt = select(MarketOverview).where(
        and_(
            MarketOverview.keyword == keyword,
            MarketOverview.marketplace == marketplace
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.total_products = overview.total_products
        existing.total_monthly_sales = overview.total_monthly_sales
        existing.total_monthly_revenue = overview.total_monthly_revenue
        existing.avg_price = overview.avg_price
        existing.min_price = overview.min_price
        existing.max_price = overview.max_price
        existing.avg_review_count = overview.avg_review_count
        existing.avg_rating = overview.avg_rating
        existing.last_updated = datetime.utcnow()
    else:
        db.add(overview)


@celery_app.task
def calculate_market_overview(keyword: str, marketplace: str = "US"):
    """定时任务：更新市场概览"""
    asyncio.run(_calculate_market_overview_async(keyword, marketplace))


async def _calculate_market_overview_async(keyword: str, marketplace: str):
    """更新市场概览的异步逻辑"""
    async with async_session_maker() as db:
        await calculate_market_for_keyword(db, keyword.lower(), marketplace)
        await db.commit()


@celery_app.task
def update_product_history(asin: str):
    """更新商品历史"""
    asyncio.run(_update_product_history_async(asin))


async def _update_product_history_async(asin: str):
    """更新商品历史的异步逻辑"""
    async with async_session_maker() as db:
        # 获取商品
        stmt = select(Product).where(Product.asin == asin)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            return
        
        # 创建历史记录
        history = ProductHistory(
            product_id=product.id,
            price=product.price,
            bsr_rank=product.bsr_rank,
            review_count=product.review_count,
            monthly_sales=product.monthly_sales,
            monthly_revenue=product.monthly_revenue,
            is_fba=product.is_fba
        )
        db.add(history)
        await db.commit()
