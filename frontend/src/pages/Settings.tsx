import { Card, Form, Input, Button, Select, Switch, Divider, message, Space, Alert } from 'antd'

export default function Settings() {
  const [form] = Form.useForm()

  const handleSave = () => {
    message.success('设置已保存')
  }

  return (
    <div>
      <Card title="⚙️ 系统设置">
        <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
          <Divider orientation="left">API 配置</Divider>

          <Form.Item label="后端 API 地址" name="apiUrl" initialValue="http://localhost:8000">
            <Input placeholder="http://localhost:8000" />
          </Form.Item>

          <Form.Item label="请求超时 (毫秒)" name="timeout" initialValue={30000}>
            <Input type="number" placeholder="30000" />
          </Form.Item>

          <Divider orientation="left">爬虫设置</Divider>

          <Form.Item label="默认市场" name="marketplace" initialValue="US">
            <Select
              options={[
                { value: 'US', label: '🇺🇸 美国 Amazon.com' },
                { value: 'UK', label: '🇬🇧 英国 Amazon.co.uk' },
                { value: 'DE', label: '🇩🇪 德国 Amazon.de' },
                { value: 'FR', label: '🇫🇷 法国 Amazon.fr' },
                { value: 'JP', label: '🇯🇵 日本 Amazon.co.jp' },
                { value: 'CA', label: '🇨🇦 加拿大 Amazon.ca' },
              ]}
            />
          </Form.Item>

          <Form.Item label="默认爬取页数" name="pages" initialValue={3}>
            <Select
              options={[
                { value: 1, label: '1 页' },
                { value: 2, label: '2 页' },
                { value: 3, label: '3 页' },
                { value: 5, label: '5 页' },
                { value: 10, label: '10 页' },
              ]}
            />
          </Form.Item>

          <Form.Item label="请求间隔 (秒)" name="delay" initialValue={3}>
            <Space>
              <Input type="number" name="minDelay" placeholder="最小" style={{ width: 80 }} />
              <span>-</span>
              <Input type="number" name="maxDelay" placeholder="最大" style={{ width: 80 }} />
            </Space>
          </Form.Item>

          <Form.Item label="使用代理" name="useProxy" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>

          <Divider orientation="left">显示设置</Divider>

          <Form.Item label="每页显示数量" name="pageSize" initialValue={20}>
            <Select
              options={[
                { value: 10, label: '10 条' },
                { value: 20, label: '20 条' },
                { value: 50, label: '50 条' },
                { value: 100, label: '100 条' },
              ]}
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" onClick={handleSave}>
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="ℹ️ 关于" style={{ marginTop: 16 }}>
        <Alert
          message="SellerSprite Clone"
          description="亚马逊选品与数据分析工具 - 开源版"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <p>版本: 1.0.0</p>
        <p>技术栈: React + TypeScript + FastAPI + PostgreSQL + Playwright</p>
        <p>
          GitHub:{' '}
          <a href="https://github.com" target="_blank" rel="noopener noreferrer">
            https://github.com
          </a>
        </p>
      </Card>
    </div>
  )
}
