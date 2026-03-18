"""
亚马逊爬虫模块
使用 Playwright 模拟真实用户行为
"""
import asyncio
import random
import re
from typing import List, Dict, Optional
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, Playwright

from app.config import settings


class AmazonScraper:
    """亚马逊爬虫类"""
    
    # 基础 URL 映射
    MARKETPLACE_URLS = {
        "US": "https://www.amazon.com",
        "UK": "https://www.amazon.co.uk",
        "DE": "https://www.amazon.de",
        "FR": "https://www.amazon.fr",
        "JP": "https://www.amazon.co.jp",
        "CA": "https://www.amazon.ca",
    }
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        
    async def __aenter__(self):
        """上下文管理器入口"""
        await self.init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        await self.close()
    
    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        
        # 启动无头浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # 生产环境设为 True
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        
        # 创建页面
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        self.page = await context.new_page()
        
        # 设置默认超时
        self.page.set_default_timeout(30000)
    
    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def _random_delay(self):
        """随机延迟"""
        delay = random.uniform(settings.min_request_delay, settings.max_request_delay)
        return delay
    
    async def _handle_popup(self):
        """处理弹窗"""
        try:
            # 关闭广告弹窗
            popup_close = self.page.locator('.a-modal-close-right, .a-popover-close, [data-action="close"]')
            if await popup_close.count() > 0:
                await popup_close.first.click()
                await asyncio.sleep(0.5)
        except:
            pass
    
    def _extract_asin(self, url: str) -> Optional[str]:
        """从 URL 提取 ASIN"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/dp%2F([A-Z0-9]{10})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """从价格文本提取数值"""
        if not price_text:
            return None
        # 匹配价格格式：$19.99, $19.99 - $29.99
        match = re.search(r'\$?([\d,]+\.?\d*)', price_text.replace(',', ''))
        if match:
            return float(match.group(1))
        return None
    
    def _estimate_monthly_sales(self, bsr_rank: int, category: str = None) -> int:
        """
        根据 BSR 排名估算月销量
        
        这是一个经验公式，实际数据可能有偏差
        """
        # 基础估算（假设 BSR 10000 ≈ 1000/月销量）
        base_sales = 10000000 / (bsr_rank + 1000)
        
        # 类目调整系数
        category_multipliers = {
            "books": 2.0,
            "electronics": 1.5,
            "clothing": 1.2,
            "home": 1.0,
            "toys": 1.3,
            "beauty": 1.1,
            "sports": 1.0,
        }
        
        if category:
            category_lower = category.lower()
            for key, mult in category_multipliers.items():
                if key in category_lower:
                    base_sales *= mult
                    break
        
        return int(base_sales)
    
    async def scrape_search_results(
        self,
        keyword: str,
        pages: int = 3,
        marketplace: str = "US"
    ) -> List[Dict]:
        """
        爬取搜索结果
        
        Args:
            keyword: 搜索关键词
            pages: 爬取页数
            marketplace: 市场（US/UK/DE等）
        
        Returns:
            商品数据列表
        """
        base_url = self.MARKETPLACE_URLS.get(marketplace, self.MARKETPLACE_URLS["US"])
        search_url = f"{base_url}/s?k={keyword.replace(' ', '+')}&rh=n:2845078031"
        
        products = []
        
        for page_num in range(1, pages + 1):
            if page_num > 1:
                # 构建分页 URL
                page_url = f"{base_url}/s?k={keyword.replace(' ', '+')}&page={page_num}"
            else:
                page_url = search_url
            
            print(f"📄 爬取第 {page_num} 页: {page_url}")
            
            # 访问页面
            await self.page.goto(page_url)
            
            # 随机延迟
            await asyncio.sleep(self._random_delay())
            
            # 处理弹窗
            await self._handle_popup()
            
            # 滚动加载更多
            await self.page.evaluate("""() => {
                window.scrollBy(0, 500);
            }""")
            await asyncio.sleep(1)
            
            # 等待商品加载
            try:
                await self.page.wait_for_selector('.s-result-item', timeout=10000)
            except:
                print(f"⚠️ 第 {page_num} 页加载超时")
                continue
            
            # 提取商品数据
            items = await self.page.query_selector_all('.s-result-item[data-asin]')
            
            for item in items:
                try:
                    # 跳过广告和无 ASIN 的项
                    asin = await item.get_attribute('data-asin')
                    if not asin or asin == 'SEARCH':
                        continue
                    
                    # 提取标题
                    title_elem = await item.query_selector('h2 a span, .a-text-normal')
                    title = await title_elem.inner_text() if title_elem else None
                    
                    # 提取价格
                    price_whole = await item.query_selector('.a-price-whole')
                    price_fraction = await item.query_selector('.a-price-fraction')
                    price_elem = await item.query_selector('.a-price')
                    
                    price = None
                    if price_whole:
                        whole = await price_whole.inner_text()
                        fraction = await price_fraction.inner_text() if price_fraction else '00'
                        price = float(f"{whole}.{fraction}")
                    elif price_elem:
                        price_text = await price_elem.inner_text()
                        price = self._extract_price(price_text)
                    
                    # 提取评分
                    rating_elem = await item.query_selector('.a-icon-alt')
                    rating = None
                    if rating_elem:
                        rating_text = await rating_elem.inner_text()
                        rating_match = re.search(r'([\d.]+)\s*out', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    
                    # 提取评论数
                    review_elem = await item.query_selector('.s-link-style .s-underline-text, .a-size-base')
                    review_count = None
                    if review_elem:
                        review_text = await review_elem.inner_text()
                        review_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
                        if review_match:
                            review_count = int(review_match.group(1))
                    
                    # 提取 BSR（Best Seller Rank）
                    bsr_elem = await item.query_selector('#spc-atf #逸生活, .a-badge-text')
                    bsr_rank = None
                    if bsr_elem:
                        bsr_text = await bsr_elem.inner_text()
                        bsr_match = re.search(r'#([\d,]+)', bsr_text)
                        if bsr_match:
                            bsr_rank = int(bsr_match.group(1).replace(',', ''))
                    
                    # 提取图片
                    img_elem = await item.query_selector('img.s-image')
                    image_url = await img_elem.get_attribute('src') if img_elem else None
                    
                    # 判断是否 FBA
                    prime_elem = await item.query_selector('.s-prime-ad, .a-icon-prime')
                    is_fba = prime_elem is not None
                    
                    # 提取详情页链接
                    link_elem = await item.query_selector('h2 a')
                    detail_url = await link_elem.get_attribute('href') if link_elem else None
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = base_url + detail_url
                    
                    # 估算月销量
                    monthly_sales = None
                    monthly_revenue = None
                    if bsr_rank:
                        monthly_sales = self._estimate_monthly_sales(bsr_rank)
                        if price and monthly_sales:
                            monthly_revenue = price * monthly_sales
                    
                    product_data = {
                        "asin": asin,
                        "title": title,
                        "price": price,
                        "rating": rating,
                        "review_count": review_count,
                        "bsr_rank": bsr_rank,
                        "monthly_sales": monthly_sales,
                        "monthly_revenue": monthly_revenue,
                        "is_fba": is_fba,
                        "image_url": image_url,
                        "detail_url": detail_url,
                        "category": None,  # 需要进入详情页获取
                        "brand": None,     # 需要进入详情页获取
                    }
                    
                    products.append(product_data)
                    
                except Exception as e:
                    print(f"⚠️ 解析商品失败: {str(e)}")
                    continue
            
            # 随机延迟，避免请求过快
            await asyncio.sleep(self._random_delay())
        
        print(f"✅ 共获取 {len(products)} 个商品")
        return products
    
    async def scrape_product_detail(self, asin: str, marketplace: str = "US") -> Dict:
        """
        爬取单个商品详情
        
        Args:
            asin: 商品 ASIN
            marketplace: 市场
        
        Returns:
            商品详情
        """
        base_url = self.MARKETPLACE_URLS.get(marketplace, self.MARKETPLACE_URLS["US"])
        detail_url = f"{base_url}/dp/{asin}"
        
        await self.page.goto(detail_url)
        await asyncio.sleep(self._random_delay())
        
        # 提取详情
        data = {"asin": asin}
        
        try:
            # 标题
            title_elem = await self.page.query_selector('#productTitle')
            if title_elem:
                data["title"] = await title_elem.inner_text()
            
            # 品牌
            brand_elem = await self.page.query_selector('#bylineInfo')
            if brand_elem:
                brand_text = await brand_elem.inner_text()
                data["brand"] = brand_text.replace('Brand: ', '').strip()
            
            # 价格
            price_elem = await self.page.query_selector('.a-price .a-offscreen')
            if price_elem:
                price_text = await price_elem.inner_text()
                data["price"] = self._extract_price(price_text)
            
            # 评分
            rating_elem = await self.page.query_selector('#averageCustomerReviews .a-icon-alt')
            if rating_elem:
                rating_text = await rating_elem.inner_text()
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    data["rating"] = float(rating_match.group(1))
            
            # 评论数
            review_elem = await self.page.query_selector('#averageCustomerReviews #acrCustomerReviewText')
            if review_elem:
                review_text = await review_elem.inner_text()
                review_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
                if review_match:
                    data["review_count"] = int(review_match.group(1))
            
            # BSR
            bsr_elem = await self.page.query_selector('#salesRank .a-text-nowrap, #detailBullets_feature_div .a-text-nowrap')
            if bsr_elem:
                bsr_text = await bsr_elem.inner_text()
                bsr_match = re.search(r'#([\d,]+)', bsr_text.replace(',', ''))
                if bsr_match:
                    data["bsr_rank"] = int(bsr_match.group(1))
            
            # 重量和尺寸
            details_elem = await self.page.query_selector('#detailBullets_feature_div')
            if details_elem:
                details_text = await details_elem.inner_text()
                
                weight_match = re.search(r'([\d.]+)\s*(kg|g|lbs|oz)', details_text, re.I)
                if weight_match:
                    weight = float(weight_match.group(1))
                    unit = weight_match.group(2).lower()
                    if unit in ['kg']:
                        data["weight_kg"] = weight
                    elif unit in ['g']:
                        data["weight_kg"] = weight / 1000
                    elif unit in ['lbs']:
                        data["weight_kg"] = weight * 0.453592
                    elif unit in ['oz']:
                        data["weight_kg"] = weight * 0.0283495
            
            # 图片
            img_elem = await self.page.query_selector('#landingImage')
            if img_elem:
                data["image_url"] = await img_elem.get_attribute('src')
            
            # 特性
            feature_elems = await self.page.query_selector_all('#feature-bullets li .a-text-bold')
            if feature_elems:
                data["features"] = [await f.inner_text() for f in feature_elems]
            
        except Exception as e:
            print(f"⚠️ 解析详情页失败: {str(e)}")
        
        return data


# 便捷函数
async def quick_scrape(keyword: str, pages: int = 3) -> List[Dict]:
    """快速爬取（上下文管理器方式）"""
    async with AmazonScraper() as scraper:
        return await scraper.scrape_search_results(keyword, pages)
