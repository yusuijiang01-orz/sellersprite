import { useState } from 'react'
import { Card, Input, Button, Row, Col, Statistic, Table, Tag, message } from 'antd'
import { SearchOutlined, ShopOutlined, DollarOutlined, BarChartOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '../api'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export default function MarketAnalysis() {
  const [keyword, setKeyword] = useState('')

  // 市场概览
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['marketOverview', keyword],
    queryFn: () => marketApi.getMarketOverview(keyword).then((res) => res.data),
    enabled: keyword.length > 0,
  })

  // 类目分析
  const { data: categories } = useQuery({
    queryKey: ['categoryAnalysis', keyword],
    queryFn: () => marketApi.getCategoryAnalysis(keyword, 10).then((res) => res.data),
    enabled: !!overview,
  })

  // 品牌分析
  const { data: brands } = useQuery({
    queryKey: ['brandAnalysis', keyword],
    queryFn: () => marketApi.getBrandAnalysis(keyword, 10).then((res) => res.data),
    enabled: !!overview,
  })

  const handleSearch = () => {
    if (!keyword.trim()) {
      message.warning('请输入关键词')
    }
  }

  const categoryColumns = [
    { title: '类目', dataIndex: 'category', key: 'category' },
    { title: '商品数', dataIndex: 'product_count', key: 'product_count' },
    { title: '均价', dataIndex: 'avg_price', key: 'avg_price', render: (v: number) => `$${v?.toFixed(2) || 0}` },
    { title: '平均月销量', dataIndex: 'avg_monthly_sales', key: 'avg_monthly_sales' },
    { title: '竞争度', dataIndex: 'competition_score', key: 'competition_score', render: (v: number) => (
      <Tag color={v > 70 ? 'red' : v > 40 ? 'orange' : 'green'}>
        {v?.toFixed(1)}%
      </Tag>
    )},
  ]

  const brandColumns = [
    { title: '品牌', dataIndex: 'brand', key: 'brand' },
    { title: '商品数', dataIndex: 'product_count', key: 'product_count' },
    { title: '均价', dataIndex: 'avg_price', key: 'avg_price', render: (v: number) => `$${v?.toFixed(2) || 0}` },
    { title: '评分', dataIndex: 'avg_rating', key: 'avg_rating', render: (v: number) => v?.toFixed(1) || '-' },
    { title: '月销量', dataIndex: 'total_monthly_sales', key: 'total_monthly_sales' },
    { title: '市场份额', dataIndex: 'market_share', key: 'market_share', render: (v: number) => `${v?.toFixed(1)}%` },
  ]

  // 价格分布数据
  const priceDistData = overview?.price_distribution
    ? Object.entries(overview.price_distribution).map(([name, value]) => ({
        name,
        value,
      }))
    : []

  return (
    <div>
      <Card title="📊 市场分析" style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="输入关键词分析市场"
          enterButton={<><SearchOutlined /> 分析</>}
          size="large"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onSearch={handleSearch}
          loading={overviewLoading}
        />
      </Card>

      {overview && (
        <>
          {/* 市场概览 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card>
                <Statistic title="商品总数" value={overview.total_products} prefix={<ShopOutlined />} />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="月总销量" value={overview.total_monthly_sales} prefix={<ShopOutlined />} />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="月销售额"
                  value={overview.total_monthly_revenue}
                  prefix="$"
                  precision={0}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic title="平均评分" value={overview.avg_rating} prefix="★" precision={1} />
              </Card>
            </Col>
          </Row>

          {/* 价格分布 & 品牌分布 */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Card title="💰 价格分布">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={priceDistData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {priceDistData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="🏢 品牌市场份额 (Top 10)">
                {brands && (
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={brands.slice(0, 8)} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="brand" width={80} />
                      <Tooltip />
                      <Bar dataKey="market_share" fill="#ff6b35" name="市场份额 %" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Card>
            </Col>
          </Row>

          {/* 类目分析 & 品牌分析 */}
          <Row gutter={16}>
            <Col span={12}>
              <Card title="📂 类目分析">
                <Table
                  columns={categoryColumns}
                  dataSource={categories}
                  rowKey="category"
                  size="small"
                  pagination={false}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="🏢 品牌分析">
                <Table
                  columns={brandColumns}
                  dataSource={brands}
                  rowKey="brand"
                  size="small"
                  pagination={false}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}

      {!keyword && (
        <Card>
          <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
            <BarChartOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>输入关键词开始市场分析</p>
          </div>
        </Card>
      )}
    </div>
  )
}
