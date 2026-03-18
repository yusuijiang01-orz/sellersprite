import { useState } from 'react'
import {
  Card,
  Input,
  Button,
  Table,
  Tag,
  Space,
  Spin,
  Alert,
  Row,
  Col,
  Statistic,
  Progress,
  Select,
  message,
} from 'antd'
import { SearchOutlined, ShopOutlined, DollarOutlined, StarOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { searchApi, marketApi } from '../api'

const { Search } = Input

interface Product {
  asin: string
  title: string
  brand: string
  price: number
  bsr_rank: number
  rating: number
  review_count: number
  monthly_sales: number
  monthly_revenue: number
  is_fba: boolean
  image_url: string
  position: number
}

interface SearchResult {
  keyword: string
  total_results: number
  products: Product[]
  market_overview: {
    total_products: number
    total_monthly_sales: number
    total_monthly_revenue: number
    avg_price: number
    avg_review_count: number
    avg_rating: number
  }
}

export default function ProductSearch() {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [marketplace, setMarketplace] = useState('US')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)

  // 创建搜索任务
  const searchMutation = useMutation({
    mutationFn: ({ keyword, marketplace }: { keyword: string; marketplace: string }) =>
      searchApi.createSearch({ keyword, marketplace, pages: 3 }),
    onSuccess: (res) => {
      setTaskId(res.data.task_id)
      message.info('搜索任务已创建，采集中...')
    },
    onError: () => {
      message.error('创建搜索任务失败')
    },
  })

  // 轮询任务状态
  const { data: taskStatus, startPolling, stopPolling } = useQuery({
    queryKey: ['searchStatus', taskId],
    queryFn: () => searchApi.getSearchStatus(taskId!).then((res) => res.data),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'done') {
        stopPolling()
        // 获取结果
        searchApi.getSearchResults(taskId!).then((res) => {
          setSearchResult(res.data)
          message.success('数据采集完成！')
        })
        return false
      }
      if (status === 'failed') {
        stopPolling()
        message.error('数据采集失败')
        return false
      }
      return 3000 // 每3秒轮询
    },
  })

  const handleSearch = () => {
    if (!keyword.trim()) {
      message.warning('请输入关键词')
      return
    }
    setSearchResult(null)
    setTaskId(null)
    searchMutation.mutate({ keyword: keyword.trim(), marketplace })
    startPolling()
  }

  const columns = [
    {
      title: '排名',
      dataIndex: 'position',
      key: 'position',
      width: 60,
    },
    {
      title: '商品',
      key: 'product',
      render: (_: unknown, record: Product) => (
        <div style={{ display: 'flex', gap: 12 }}>
          {record.image_url && (
            <img
              src={record.image_url}
              alt={record.title}
              style={{ width: 60, height: 60, objectFit: 'contain' }}
            />
          )}
          <div style={{ maxWidth: 300 }}>
            <div
              style={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                cursor: 'pointer',
                color: '#1890ff',
              }}
              onClick={() => navigate(`/product/${record.asin}`)}
            >
              {record.title}
            </div>
            <div style={{ fontSize: 12, color: '#888' }}>{record.asin}</div>
            {record.brand && <Tag style={{ marginTop: 4 }}>{record.brand}</Tag>}
          </div>
        </div>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number) =>
        price ? <span className="price-tag">${price.toFixed(2)}</span> : '-',
    },
    {
      title: 'BSR',
      dataIndex: 'bsr_rank',
      key: 'bsr_rank',
      width: 80,
      render: (rank: number) => (rank ? `#${rank.toLocaleString()}` : '-'),
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      width: 100,
      render: (rating: number) =>
        rating ? (
          <span>
            <span className="star-rating">★</span> {rating.toFixed(1)}
          </span>
        ) : (
          '-'
        ),
    },
    {
      title: '评论数',
      dataIndex: 'review_count',
      key: 'review_count',
      width: 100,
      render: (count: number) => (count ? count.toLocaleString() : '-'),
    },
    {
      title: '月销量',
      dataIndex: 'monthly_sales',
      key: 'monthly_sales',
      width: 100,
      render: (sales: number) => (sales ? sales.toLocaleString() : '-'),
    },
    {
      title: '月销售额',
      dataIndex: 'monthly_revenue',
      key: 'monthly_revenue',
      width: 120,
      render: (revenue: number) =>
        revenue ? <span>${revenue.toLocaleString()}</span> : '-',
    },
    {
      title: 'FBA',
      dataIndex: 'is_fba',
      key: 'is_fba',
      width: 60,
      render: (isFba: boolean) => (isFba ? <span className="fba-badge">FBA</span> : '-'),
    },
  ]

  return (
    <div>
      <Card title="🛒 选品搜索" style={{ marginBottom: 16 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Select
            value={marketplace}
            onChange={setMarketplace}
            style={{ width: 100 }}
            options={[
              { value: 'US', label: '🇺🇸 美国' },
              { value: 'UK', label: '🇬🇧 英国' },
              { value: 'DE', label: '🇩🇪 德国' },
              { value: 'FR', label: '🇫🇷 法国' },
              { value: 'JP', label: '🇯🇵 日本' },
            ]}
          />
          <Search
            placeholder="输入关键词，如: yoga mat"
            allowClear
            enterButton={<><SearchOutlined /> 搜索</>}
            size="large"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={handleSearch}
            loading={searchMutation.isPending}
          />
        </Space.Compact>
      </Card>

      {/* 搜索状态 */}
      {taskId && !searchResult && (
        <Card style={{ marginBottom: 16 }}>
          <Spin tip="数据采集中，请稍候...">
            <div style={{ padding: 40, textAlign: 'center' }}>
              <p>任务状态: {taskStatus?.status || 'pending'}</p>
              <p>已采集: {taskStatus?.result_count || 0} 个商品</p>
            </div>
          </Spin>
        </Card>
      )}

      {/* 搜索结果 */}
      {searchResult && (
        <>
          {/* 市场概览 */}
          {searchResult.market_overview && (
            <Card title="📊 市场概览" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="商品总数"
                    value={searchResult.market_overview.total_products}
                    prefix={<ShopOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="月总销量"
                    value={searchResult.market_overview.total_monthly_sales}
                    prefix={<ShopOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="月总销售额"
                    value={searchResult.market_overview.total_monthly_revenue}
                    prefix={<DollarOutlined />}
                    precision={0}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="平均评分"
                    value={searchResult.market_overview.avg_rating}
                    prefix={<StarOutlined />}
                    precision={1}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* 商品列表 */}
          <Card title={`📋 商品列表 (${searchResult.total_results})`}>
            <Table
              columns={columns}
              dataSource={searchResult.products}
              rowKey="asin"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 个商品`,
              }}
              scroll={{ x: 1200 }}
              size="small"
            />
          </Card>
        </>
      )}

      {/* 初始提示 */}
      {!taskId && !searchResult && (
        <Alert
          message="欢迎使用选品搜索"
          description="输入关键词开始搜索，如 'yoga mat'、'wireless earbuds' 等"
          type="info"
          showIcon
        />
      )}
    </div>
  )
}
