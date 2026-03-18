# 🎯 SellerSprite 快速部署指南

## 问题快速解答

### ❌ 你遇到的错误
```
bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/blob/main/sellersprite/deploy-from-github.sh)
/dev/fd/63: line 1: 404:: command not found
```

### ✅ 原因和解决方案

**原因**：URL 路径使用了 `/blob/main/` 而不是 `/raw/main/`

**修复**：只需将 URL 中的 `blob` 改成 `raw`

---

## 🚀 立即部署（3 种方式）

### 方式 1：一键部署（推荐）✨

```bash
# 在服务器上运行此命令
bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh)
```

**就这么简单！** 脚本会自动处理所有部署步骤。

### 方式 2：分步手动部署

如果你想手动控制每一步：

```bash
# 1. 进入服务器
ssh root@103.53.81.226

# 2. 安装依赖
sudo apt update && sudo apt install -y git docker.io docker-compose

# 3. 克隆项目
cd /opt && git clone https://github.com/yusuijiang01-orz/sellersprite.git
cd sellersprite/sellersprite

# 4. 配置环境
cp .env.example .env
nano .env  # 编辑并设置密码

# 5. 启动服务
docker-compose up -d

# 6. 等待服务启动
sleep 15

# 7. 验证部署
docker-compose ps
curl http://localhost:8000/health
```

### 方式 3：使用改进的脚本

我为你生成了一个改进的 `deploy-from-github.sh` 脚本，包含：
- ✅ 自动环境检查
- ✅ 详细的进度提示
- ✅ 自动故障排查
- ✅ 部署完成验证

**该脚本已保存到**：`d:\App\sellersprite\sellersprite\deploy-from-github.sh`

---

## 📊 部署后的验证

部署完成后，检查以下内容：

```bash
# 1. 查看容器状态
cd /opt/sellersprite/sellersprite
docker-compose ps

# 2. 测试 API
curl http://localhost:8000/health
# 预期输出: {"status": "healthy"}

# 3. 查看日志
docker-compose logs -f api

# 4. 访问 API 文档
# 在浏览器打开: http://103.53.81.226:8000/docs
```

---

## 🔍 关键 URL 对比

| 说明 | URL | 能否用于 bash |
|------|-----|-------------|
| ✅ **正确** | `raw.githubusercontent.com/.../raw/main/file.sh` | ✅ YES |
| ❌ **错误** | `raw.githubusercontent.com/.../blob/main/file.sh` | ❌ NO (404) |
| ❌ **错误** | `github.com/.../blob/main/file.sh` | ❌ NO (HTML) |

---

## 🆘 常见问题

### Q: 还是出现 404 错误？
**A**: 确保 URL 中使用的是 `/raw/main/` 而不是 `/blob/main/`

### Q: 部署后 API 无法连接？
**A**: 运行 `docker-compose logs api` 查看错误，或查看 `DEPLOYMENT-TROUBLESHOOTING.md`

### Q: 如何修改数据库密码？
**A**: 
1. 编辑 `.env` 文件
2. 运行 `docker-compose restart postgres redis`
3. 重新初始化数据库（如需要）

### Q: 部署在哪个目录？
**A**: `/opt/sellersprite/sellersprite/`（假设使用默认配置）

### Q: 如何查看实时日志？
**A**: `docker-compose logs -f api`（持续显示 API 日志）

---

## 📁 重要文件

| 文件 | 位置 | 用途 |
|------|------|------|
| **deploy-from-github.sh** | 项目根 | 自动化部署脚本 |
| **.env.example** | 项目根 | 环境变量模板 |
| **.env** | 项目根 | 实际环境配置（生产密码） |
| **docker-compose.yml** | 项目根 | Docker 容器编排 |
| **DEPLOYMENT-TROUBLESHOOTING.md** | 项目根 | 故障排查指南 |
| **DEPLOYMENT.md** | 项目根 | 完整部署指南 |

---

## ⚡ 快速命令参考

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs

# 查看 API 日志
docker-compose logs api

# 进入 API 容器
docker-compose exec api bash

# 测试 API 连接
curl http://localhost:8000/health

# 测试 Redis
docker-compose exec redis redis-cli ping

# 查看进程
docker-compose ps -a
```

---

## 🎓 关键概念解释

### 什么是 /raw/main/?
- `raw` = 原始文件内容（纯文本）
- `main` = 分支名称
- 这是 GitHub 提供的用于下载原始文件的 URL 格式

### 什么是 /blob/main/?
- `blob` = GitHub 网页展示格式
- 返回的是 HTML 网页，不能直接作为脚本运行

### 为什么会出现 404 错误？
- 当 `curl` 尝试下载一个不存在的文件时会返回 404
- 如果使用了错误的 URL 格式，curl 会接收到错误页面
- bash 尝试运行 HTML 错误页面就会出现"404:: command not found"

---

## 💡 下一步建议

### 立即完成
1. ✅ 使用正确的 URL 运行部署
2. ✅ 验证所有服务都在运行
3. ✅ 访问 API 文档测试功能

### 部署后
1. ✅ 修改默认密码为强密码
2. ✅ 配置 SSL 证书（HTTPS）
3. ✅ 设置自动备份
4. ✅ 配置监控告警

### 长期维护
1. ✅ 定期更新代码：`git pull`
2. ✅ 监控日志和性能
3. ✅ 定期数据库备份
4. ✅ 安全更新

---

## 📞 获取帮助

如果遇到问题：

1. **查看日志**：`docker-compose logs -f`
2. **查看文档**：
   - `DEPLOYMENT-TROUBLESHOOTING.md` - 故障排查
   - `DEPLOYMENT.md` - 完整指南
   - `QUICK-START.md` - 快速开始
3. **运行诊断**：`bash redis-diagnosis.sh`（如果存在）

---

## 🎉 预期结果

成功部署后，你应该看到：

```
✅ 部署完成！

📍 访问地址:
   API 文档:    http://103.53.81.226:8000/docs
   健康检查:    http://103.53.81.226:8000/health

🔧 常用命令:
   查看日志:     docker-compose logs -f api
   重启服务:     docker-compose restart
   停止服务:     docker-compose down
```

---

**祝你部署顺利！** 🚀
