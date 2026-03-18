import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Tag, Spin, Descriptions, Button, Statistic, Modal, InputNumber, message, Form, Space } from 'antd'
import { ArrowLeftOutlined, ShopOutlined, DollarOutlined, StarOutlined, TruckOutlined } from '@ant-design/icons'
import { productApi, fbaApi } from '../api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ProductDetail() {
  const { asin } = useParams<{ asin: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()

  // 获取商品详情
  const { data: product, isLoading } = useQuery({
    queryKey: ['product', asin],
    queryFn: () => productApi.getProductDetail(asin!).then((res) => res.data),
    enabled: !!asin,
  })

  // 获取商品历史
  const { data: history } = useQuery({
    queryKey: ['productHistory', asin],
    queryFn: () => productApi.getProductHistory(asin!, 30).then((res) => res.data),
    enabled: !!asin,
  })

  // FBA 估算
  const [fbaModalOpen, setFbaModalOpen] = useState(false)
  const [fbaResult, setFbaResult] = useState<any>(null)

  const handleFbaEstimate = async (values: any) => {
    try {
      const res = await fbaApi.estimateFba({
        asin: asin!,
        cost_price: values.cost_price,
        shipping_cost: values.shipping_cost || 0,
        selling_price: values.selling_price,
        category: values.category || 'general',
      })
      setFbaResult(res.data)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '估算失败')
    }
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!product) {
    return <Card>商品不存在</Card>
  }

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={{ marginBottom: 16 }}>
        返回搜索
      </Button>

      <Row gutter={16}>
        {/* 左侧：商品信息 */}
        <Col span={16}>
          <Card title={`${product.asin} - ${product.title}`}>
            <Row gutter={16}>
              <Col span={8}>
                {product.image_url && (
                  <img src={product.image_url} alt={product.title} style={{ width: '100%' }} />
                )}
              </Col>
              <Col span={16}>
                <Descriptions column={1}>
                  <Descriptions.Item label="品牌">{product.brand || '-'}</Descriptions.Item>
                  <Descriptions.Item label="类目">{product.category || '-'}</Descriptions.Item>
                  <Descriptions.Item label="BSR排名">
                    {product.bsr_rank ? `#${product.bsr_rank.toLocaleString()}` : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="BSR类目">{product.bsr_category || '-'}</Descriptions.Item>
                  <Descriptions.Item label="评分">
                    {product.rating ? (
                      <span>
                        <span style={{ color: '#faad14' }}>★</span> {product.rating.toFixed(1)}
                      </span>
                    ) : (
                      '-'
                    )}
                  </Descriptions.Item>
                  <Descriptions.Item label="评论数">
                    {product.review_count ? product.review_count.toLocaleString() : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="卖家数量">{product.seller_count || '-'}</Descriptions.Item>
                  <Descriptions.Item label="配送方式">
                    <Tag color={product.is_fba ? 'green' : 'default'}>{product.is_fba ? 'FBA' : '自配送'}</Tag>
                    {product.is_prime && <Tag color="blue">Prime</Tag>}
                  </Descriptions.Item>
                  <Descriptions.Item label="重量">{product.weight_kg ? `${product.weight_kg} kg` : '-'}</Descriptions.Item>
                  <Descriptions.Item label="尺寸">{product.dimensions || '-'}</Descriptions.Item>
                </Descriptions>

                <Button type="primary" onClick={() => setFbaModalOpen(true)} style={{ marginTop: 16 }}>
                  💰 FBA 利润估算
                </Button>
              </Col>
            </Row>
          </Card>

          {/* 历史趋势 */}
          {history?.history && history.history.length > 0 && (
            <Card title="📈 价格/销量趋势 (30天)" style={{ marginTop: 16 }}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history.history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(v) => v?.slice(5, 10)} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Line yAxisId="left" type="monotone" dataKey="price" name="价格" stroke="#ff6b35" />
                  <Line yAxisId="right" type="monotone" dataKey="monthly_sales" name="月销量" stroke="#1890ff" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}
        </Col>

        {/* 右侧：销售估算 */}
        <Col span={8}>
          <Card title="📊 销售估算" style={{ marginBottom: 16 }}>
            <Statistic
              title="售价"
              value={product.price}
              prefix="$"
              valueStyle={{ color: '#ff6b35', fontSize: 28 }}
            />
          </Card>

          <Card title="📈 月度数据" style={{ marginBottom: 16 }}>
            <Statistic title="月销量估算" value={product.monthly_sales} prefix={<ShopOutlined />} />
            <Statistic
              title="月销售额"
              value={product.monthly_revenue}
              prefix="$"
              precision={0}
              style={{ marginTop: 16 }}
            />
          </Card>

          {product.detail_url && (
            <Card>
              <Button type="primary" block onClick={() => window.open(product.detail_url, '_blank')}>
                在亚马逊查看
              </Button>
            </Card>
          )}
        </Col>
      </Row>

      {/* FBA 估算弹窗 */}
      <Modal
        title="💰 FBA 利润估算"
        open={fbaModalOpen}
        onCancel={() => setFbaModalOpen(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleFbaEstimate}>
          <Form.Item name="cost_price" label="成本价 ($)" rules={[{ required: true }]}>
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} placeholder="如: 8.5" />
          </Form.Item>
          <Form.Item name="shipping_cost" label="头程运费 ($)">
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} placeholder="如: 2.0" />
          </Form.Item>
          <Form.Item name="selling_price" label="售价 ($)（留空使用当前售价）">
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} placeholder={`当前: ${product.price}`} />
          </Form.Item>
          <Form.Item name="category" label="类目">
            <Select
              options={[
                { value: 'general', label: '一般品类 (15%)' },
                { value: 'electronics', label: '电子产品 (8%)' },
                { value: 'clothing', label: '服装 (15%)' },
                { value: 'jewelry', label: '珠宝 (20%)' },
                { value: 'beauty', label: '美妆 (15%)' },
                { value: 'toys', label: '玩具 (15%)' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={false}>
              开始估算
            </Button>
          </Form.Item>
        </Form>

        {fbaResult && (
          <Card style={{ marginTop: 16, background: '#f6ffed' }}>
            <Statistic
              title="预估利润"
              value={fbaResult.estimated_profit}
              prefix="$"
              valueStyle={{ color: '#52c41a', fontSize: 24 }}
            />
            <Statistic title="利润率" value={fbaResult.profit_margin} suffix="%" style={{ marginTop: 8 }} />
            <Descriptions column={1} size="small" style={{ marginTop: 16 }}>
              <Descriptions.Item label="售价">{fbaResult.selling_price}</Descriptions.Item>
              <Descriptions.Item label="成本">{fbaResult.cost_price}</Descriptions.Item>
              <Descriptions.Item label="佣金">{fbaResult.referral_fee}</Descriptions.Item>
              <Descriptions.Item label="FBA配送费">{fbaResult.fba_delivery_fee}</Descriptions.Item>
              <Descriptions.Item label="仓储费">{fbaResult.storage_fee}</Descriptions.Item>
              <Descriptions.Item label="总成本">{fbaResult.total_cost}</Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Modal>
    </div>
  )
}

// 导入 useState
import { useState } from 'react'
