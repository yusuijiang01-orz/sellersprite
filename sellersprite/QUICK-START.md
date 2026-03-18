# GitHub 部署快速参考卡 - 一页纸总结

## 🎯 核心流程（3 步）

```
本地代码 → GitHub 仓库 → Debian 服务器
   ↓          ↓            ↓
git push    创建仓库    一键部署脚本
```

---

## 📋 第 1 步：上传到 GitHub（本地执行）

### 1.1 创建 GitHub 仓库
访问 https://github.com/new，创建新仓库 `sellersprite`

### 1.2 本地初始化 Git
```bash
cd d:/App/sellersprite
git init
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 1.3 提交并推送
```bash
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/sellersprite.git
git branch -M main
git push -u origin main
```

✅ 验证：访问 https://github.com/你的用户名/sellersprite 查看代码

---

## 📦 第 2 步：在服务器上部署

### 方式 A：一键部署（⭐ 推荐）
```bash
# 登录服务器
ssh root@103.53.81.226

# 一键部署
bash <(curl -sL https://raw.githubusercontent.com/你的用户名/sellersprite/main/deploy-from-github.sh)

# 按提示输入参数
```

### 方式 B：手动部署
```bash
ssh root@103.53.81.226
cd /opt
git clone https://github.com/你的用户名/sellersprite.git
cd sellersprite
cp .env.example .env
docker-compose up -d
```

---

## ✅ 第 3 步：验证部署成功

```bash
# 检查容器状态
docker-compose ps

# 测试 API
curl http://localhost:8000/health

# 查看 API 文档
# 浏览器访问：http://103.53.81.226:8000/docs
```

---

## 🔄 后续操作

### 更新代码
```bash
cd /opt/sellersprite
git pull
docker-compose up -d --build
```

### 常用命令
```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

---

## 🔑 关键点

| 项目 | 值 |
|------|---|
| 服务器 IP | 103.53.81.226 |
| 登录用户 | root |
| 部署目录 | /opt/sellersprite |
| API 端口 | 8000 |
| API 文档 | http://103.53.81.226:8000/docs |

---

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `deploy-from-github.sh` | 一键部署脚本 |
| `docker-compose.yml` | Docker 配置 |
| `.env.example` | 环境变量模板 |
| `GITHUB-DEPLOYMENT.md` | 详细部署指南 |
| `GITHUB-WORKFLOW.md` | 完整工作流程 |

---

## 🆘 快速故障排查

| 问题 | 命令 |
|------|------|
| 容器无法启动 | `docker-compose logs` |
| Redis 连接失败 | `docker-compose exec redis redis-cli ping` |
| 端口被占用 | `lsof -i :8000` |
| 查看所有服务 | `docker-compose ps` |

---

## 💡 记住这 3 个命令

```bash
# 1. 查看状态
docker-compose ps

# 2. 查看日志
docker-compose logs -f

# 3. 重启服务
docker-compose restart
```

---

**立即开始部署！** 🚀

