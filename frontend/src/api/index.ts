import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 搜索相关
export const searchApi = {
  // 创建搜索任务
  createSearch: (data: { keyword: string; marketplace?: string; pages?: number }) =>
    api.post('/search', data),

  // 获取搜索状态
  getSearchStatus: (taskId: string) => api.get(`/search/${taskId}`),

  // 获取搜索结果
  getSearchResults: (taskId: string) => api.get(`/search/${taskId}/results`),
}

// 商品相关
export const productApi = {
  // 获取商品列表
  getProducts: (params: {
    keyword?: string
    min_price?: number
    max_price?: number
    min_monthly_sales?: number
    max_monthly_sales?: number
    min_review_count?: number
    max_review_count?: number
    min_rating?: number
    is_fba?: boolean
    sort_by?: string
    sort_order?: string
    page?: number
    page_size?: number
  }) => api.get('/products', { params }),

  // 获取商品详情
  getProductDetail: (asin: string) => api.get(`/products/${asin}`),

  // 获取商品历史
  getProductHistory: (asin: string, days?: number) =>
    api.get(`/products/${asin}/history`, { params: { days } }),
}

// 市场相关
export const marketApi = {
  // 获取市场概览
  getMarketOverview: (keyword: string, marketplace?: string) =>
    api.get('/market/overview', { params: { keyword, marketplace } }),

  // 获取类目分析
  getCategoryAnalysis: (keyword: string, limit?: number) =>
    api.get('/market/categories', { params: { keyword, limit } }),

  // 获取品牌分析
  getBrandAnalysis: (keyword: string, limit?: number) =>
    api.get('/market/brands', { params: { keyword, limit } }),
}

// FBA 估算
export const fbaApi = {
  // 估算 FBA 费用
  estimateFba: (data: {
    asin: string
    cost_price: number
    shipping_cost?: number
    selling_price?: number
    category?: string
  }) => api.post('/fba/estimate', data),

  // 获取费率表
  getFeeTable: () => api.get('/fba/fees'),
}

export default api
