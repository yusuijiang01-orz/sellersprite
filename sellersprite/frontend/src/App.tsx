import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  SearchOutlined,
  ShopOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

import ProductSearch from './pages/ProductSearch'
import ProductDetail from './pages/ProductDetail'
import MarketAnalysis from './pages/MarketAnalysis'
import Settings from './pages/Settings'

const { Header, Sider, Content } = Layout

function App() {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    {
      key: '/',
      icon: <SearchOutlined />,
      label: '选品搜索',
    },
    {
      key: '/market',
      icon: <BarChartOutlined />,
      label: '市场分析',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <div style={{ fontSize: 20, fontWeight: 'bold', color: '#ff6b35' }}>
          🛒 SellerSprite Clone
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              background: '#fff',
              padding: 24,
              margin: 0,
              minHeight: 280,
            }}
          >
            <Routes>
              <Route path="/" element={<ProductSearch />} />
              <Route path="/product/:asin" element={<ProductDetail />} />
              <Route path="/market" element={<MarketAnalysis />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default App
