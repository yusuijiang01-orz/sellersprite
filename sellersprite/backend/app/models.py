"""
SellerSprite Clone - 数据库模型
亚马逊选品与数据分析工具
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Index, UniqueConstraint, JSON, Numeric
)
from sqlalchemy.orm import relationship

from app.database import Base


class Keyword(Base):
    """关键词表"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    search_volume = Column(Integer, nullable=True, comment="月搜索量")
    competition = Column(Float, nullable=True, comment="竞争指数 0~1")
    trend_data = Column(JSON, nullable=True, comment="近12个月趋势数组")
    marketplace = Column(String(10), default="US", index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    products = relationship("KeywordProduct", back_populates="keyword")


class Product(Base):
    """商品表"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    category_id = Column(String(50), nullable=True)
    
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD")
    bsr_rank = Column(Integer, nullable=True, index=True)
    bsr_category = Column(String(100), nullable=True)
    
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True, index=True)
    
    monthly_sales = Column(Integer, nullable=True, comment="月销量估算")
    monthly_revenue = Column(Numeric(12, 2), nullable=True, comment="月销售额估算")
    
    image_url = Column(Text, nullable=True)
    detail_url = Column(Text, nullable=True)
    
    is_fba = Column(Boolean, default=False, index=True)
    is_prime = Column(Boolean, default=False)
    seller_count = Column(Integer, nullable=True)
    
    weight_kg = Column(Float, nullable=True, comment="商品重量")
    dimensions = Column(String(100), nullable=True, comment="尺寸 LxWxH cm")
    
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True, comment="产品特性数组")
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    keyword_products = relationship("KeywordProduct", back_populates="product")
    histories = relationship("ProductHistory", back_populates="product")
    fba_estimates = relationship("FbaEstimate", back_populates="product")

    __table_args__ = (
        Index("idx_products筛选", "price", "monthly_sales", "review_count"),
    )


class KeywordProduct(Base):
    """关键词与商品关联表"""
    __tablename__ = "keyword_products"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    position = Column(Integer, nullable=True, comment="搜索结果排名位置")
    page = Column(Integer, default=1, comment="第几页")
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    keyword = relationship("Keyword", back_populates="products")
    product = relationship("Product", back_populates="keyword_products")

    __table_args__ = (
        UniqueConstraint("keyword_id", "product_id", name="uq_keyword_product"),
    )


class ProductHistory(Base):
    """商品历史记录表"""
    __tablename__ = "product_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    price = Column(Numeric(10, 2), nullable=True)
    bsr_rank = Column(Integer, nullable=True)
    bsr_category = Column(String(100), nullable=True)
    review_count = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    monthly_sales = Column(Integer, nullable=True)
    monthly_revenue = Column(Numeric(12, 2), nullable=True)
    
    is_fba = Column(Boolean, default=False)
    seller_count = Column(Integer, nullable=True)
    
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关联
    product = relationship("Product", back_populates="histories")

    __table_args__ = (
        Index("idx_history_product_time", "product_id", "recorded_at"),
    )


class FbaEstimate(Base):
    """FBA费用估算表"""
    __tablename__ = "fba_estimates"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # 成本
    cost_price = Column(Numeric(10, 2), nullable=True, comment="成本价")
    shipping_cost = Column(Numeric(8, 2), nullable=True, comment="头程运费")
    
    # 亚马逊费用
    referral_fee = Column(Numeric(8, 2), nullable=True, comment="亚马逊佣金")
    fba_fee = Column(Numeric(8, 2), nullable=True, comment="FBA配送费")
    storage_fee = Column(Numeric(8, 2), nullable=True, comment="月仓储费")
    commission_rate = Column(Float, default=0.15, comment="佣金比例")
    
    # 尺寸等级
    weight_kg = Column(Float, nullable=True)
    size_tier = Column(String(50), nullable=True)
    
    # 计算结果
    total_fba_cost = Column(Numeric(8, 2), nullable=True)
    estimated_profit = Column(Numeric(8, 2), nullable=True, comment="估算利润")
    profit_margin = Column(Float, nullable=True, comment="利润率 %")
    
    sell_price = Column(Numeric(10, 2), nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    product = relationship("Product", back_populates="fba_estimates")


class ScrapeTask(Base):
    """爬虫任务表"""
    __tablename__ = "scrape_tasks"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    marketplace = Column(String(10), default="US")
    
    status = Column(String(20), default="pending", index=True)  # pending/running/done/failed
    task_id = Column(String(100), nullable=True, index=True)
    
    pages = Column(Integer, default=3)
    result_count = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class MarketOverview(Base):
    """市场概览缓存表"""
    __tablename__ = "market_overview"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    marketplace = Column(String(10), default="US")
    
    # 市场容量
    total_products = Column(Integer, nullable=True)
    total_monthly_sales = Column(Integer, nullable=True)
    total_monthly_revenue = Column(Numeric(14, 2), nullable=True)
    
    # 价格分布
    avg_price = Column(Numeric(10, 2), nullable=True)
    min_price = Column(Numeric(10, 2), nullable=True)
    max_price = Column(Numeric(10, 2), nullable=True)
    
    # 竞争分析
    avg_review_count = Column(Float, nullable=True)
    avg_rating = Column(Float, nullable=True)
    top_10_concentration = Column(Float, nullable=True, comment="头部10%占比")
    
    # 数据
    price_distribution = Column(JSON, nullable=True)
    brand_distribution = Column(JSON, nullable=True)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Skill(Base):
    """技能表 - Roguelike元素"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    skill_type = Column(String(20), nullable=False)  # jump/gravity/special
    level = Column(Integer, default=1)
    max_level = Column(Integer, default=5)
    unlock_score = Column(Integer, default=0)
    cost = Column(Integer, default=0)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserProgress(Base):
    """用户进度表 - 故事系统"""
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    od_id = Column(String(50), nullable=True, index=True)  # 微信OpenID
    
    total_score = Column(Integer, default=0)
    highest_score = Column(Integer, default=0)
    total_jumps = Column(Integer, default=0)
    total_distance = Column(Float, default=0)
    
    unlocked_skills = Column(JSON, default=list)
    current_chapter = Column(Integer, default=1)
    unlocked_fragments = Column(JSON, default=list)
    
    achievements = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
