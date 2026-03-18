"""
FBA 估算 API - 亚马逊物流费用计算
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Product, FbaEstimate

router = APIRouter()


# ============ Constants - 亚马逊费率表 ============

# 佣金比例（类目不同比例不同）
REFERRAL_FEES = {
    "general": 0.15,        # 一般品类 15%
    "electronics": 0.08,    # 电子产品 8%
    "clothing": 0.15,       # 服装 15%
    "jewelry": 0.20,        # 珠宝 20%
    "beauty": 0.15,         # 美妆 15%
    "toys": 0.15,          # 玩具 15%
    "sports": 0.15,         # 运动 15%
    "books": 0.15,          # 书籍 15%
}

# FBA 配送费（按尺寸等级，单位：美元）
# 小号标准件
FBA_FEES_SMALL_STANDARD = {
    "1": 3.22,
    "2": 3.22,
    "3": 4.24,
    "4": 4.24,
}

# 大号标准件
FBA_FEES_LARGE_STANDARD = {
    "1": 5.26,
    "2": 5.74,
    "3": 6.06,
    "4": 7.30,
}

# 大件商品
FBA_FEES_BULKY = {
    "1": 9.99,
    "2": 15.05,
}


# ============ Request/Response Models ============

class FbaEstimateRequest(BaseModel):
    """FBA 估算请求"""
    asin: str
    cost_price: float = Query(..., ge=0, description="成本价")
    shipping_cost: float = Query(0, ge=0, description="头程运费")
    selling_price: Optional[float] = Query(None, description="售价（留空则使用商品当前售价）")
    category: str = Query("general", description="类目")


class FbaEstimateResponse(BaseModel):
    """FBA 估算响应"""
    asin: str
    product_name: str
    
    # 输入参数
    cost_price: float
    selling_price: float
    shipping_cost: float
    
    # 亚马逊费用明细
    referral_fee: float
    fba_delivery_fee: float
    storage_fee: float
    total_amazon_fees: float
    
    # 计算结果
    total_cost: float
    estimated_profit: float
    profit_margin: float
    
    # 尺寸信息
    weight_kg: Optional[float]
    size_tier: Optional[str]
    
    class Config:
        from_attributes = True


# ============ Helper Functions ============

def calculate_referral_fee(price: float, category: str = "general") -> float:
    """计算佣金"""
    rate = REFERRAL_FEES.get(category, REFERRAL_FEES["general"])
    # 佣金有最低$0.30
    return max(price * rate, 0.30)


def calculate_fba_fee(weight_kg: float, dimensions: Optional[str] = None) -> float:
    """计算 FBA 配送费"""
    if not weight_kg:
        return 5.50  # 默认费用
    
    # 简单估算：按重量阶梯
    if weight_kg <= 0.25:
        return 3.22
    elif weight_kg <= 0.5:
        return 4.24
    elif weight_kg <= 1.0:
        return 5.26
    elif weight_kg <= 1.5:
        return 5.74
    elif weight_kg <= 2.0:
        return 6.06
    elif weight_kg <= 3.0:
        return 7.30
    elif weight_kg <= 5.0:
        return 9.99
    else:
        return 15.05


def calculate_storage_fee(volume_m3: float = 0.001) -> float:
    """计算月仓储费"""
    # 标准件: $0.75/立方英尺/月
    # 转换为立方米: 1立方英尺 = 0.0283立方米
    # 约 $26.5/立方米/月
    return volume_m3 * 26.5


# ============ API Routes ============

@router.post("/fba/estimate", response_model=FbaEstimateResponse)
async def estimate_fba(
    request: FbaEstimateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    FBA 费用估算
    
    根据商品信息和成本计算利润
    """
    # 1. 获取商品信息
    stmt = select(Product).where(Product.asin == request.asin.upper())
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 2. 确定售价
    selling_price = request.selling_price
    if selling_price is None:
        if not product.price:
            raise HTTPException(status_code=400, detail="商品无售价，请手动输入")
        selling_price = float(product.price)
    
    # 3. 计算各项费用
    # 佣金
    referral_fee = calculate_referral_fee(selling_price, request.category)
    
    # FBA 配送费
    fba_delivery_fee = calculate_fba_fee(
        product.weight_kg,
        product.dimensions
    )
    
    # 仓储费（简单估算）
    storage_fee = calculate_storage_fee()
    
    # 总亚马逊费用
    total_amazon_fees = referral_fee + fba_delivery_fee + storage_fee
    
    # 总成本
    total_cost = request.cost_price + request.shipping_cost + total_amazon_fees
    
    # 利润
    estimated_profit = selling_price - total_cost
    
    # 利润率
    profit_margin = (estimated_profit / selling_price * 100) if selling_price > 0 else 0
    
    # 4. 保存估算记录
    estimate = FbaEstimate(
        product_id=product.id,
        cost_price=request.cost_price,
        shipping_cost=request.shipping_cost,
        referral_fee=referral_fee,
        fba_fee=fba_delivery_fee,
        storage_fee=storage_fee,
        sell_price=selling_price,
        total_fba_cost=total_amazon_fees,
        estimated_profit=estimated_profit,
        profit_margin=profit_margin,
        weight_kg=product.weight_kg,
        size_tier=product.dimensions
    )
    db.add(estimate)
    await db.commit()
    
    return FbaEstimateResponse(
        asin=product.asin,
        product_name=product.title or "",
        cost_price=request.cost_price,
        selling_price=selling_price,
        shipping_cost=request.shipping_cost,
        referral_fee=round(referral_fee, 2),
        fba_delivery_fee=round(fba_delivery_fee, 2),
        storage_fee=round(storage_fee, 2),
        total_amazon_fees=round(total_amazon_fees, 2),
        total_cost=round(total_cost, 2),
        estimated_profit=round(estimated_profit, 2),
        profit_margin=round(profit_margin, 1),
        weight_kg=product.weight_kg,
        size_tier=product.dimensions
    )


@router.get("/fba/fees")
async def get_fba_fee_table():
    """
    获取 FBA 费率表
    
    返回参考费率信息
    """
    return {
        "referral_fees": REFERRAL_FEES,
        "fba_delivery_fees": {
            "small_standard": FBA_FEES_SMALL_STANDARD,
            "large_standard": FBA_FEES_LARGE_STANDARD,
            "bulky": FBA_FEES_BULKY
        },
        "storage_fees": {
            "standard": "$0.75/立方英尺/月",
            "oversize": "$0.75/立方英尺/月"
        },
        "note": "实际费用可能因亚马逊政策调整而变化，请以亚马逊后台为准"
    }
