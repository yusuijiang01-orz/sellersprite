# 📍 SellerSprite 部署 - 一页纸快速指南

## 🔴 问题
```
/dev/fd/63: line 1: 404:: command not found
```

## ✅ 解决（3 种方式）

### 方式 1：一条命令
```bash
bash <(curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh)
```

### 方式 2：分步部署
```bash
ssh root@103.53.81.226
cd /opt && git clone https://github.com/yusuijiang01-orz/sellersprite.git
cd sellersprite/sellersprite
cp .env.example .env && nano .env    # 修改密码
docker-compose up -d
sleep 15 && docker-compose ps
curl http://localhost:8000/health
```

### 方式 3：验证后部署
```bash
curl -sL https://raw.githubusercontent.com/yusuijiang01-orz/sellersprite/main/sellersprite/deploy-from-github.sh -o deploy.sh
head -5 deploy.sh  # 验证不是 404
sudo bash deploy.sh
```

## 🔍 关键点

| 项目 | 详情 |
|------|------|
| **正确 URL** | `raw.githubusercontent.com/.../raw/main/...` |
| **错误 URL** | `raw.githubusercontent.com/.../blob/main/...` |
| **部署时间** | 3-5 分钟 |
| **成功标志** | 所有容器都 "Up"，API 返回 200 |
| **访问地址** | `http://103.53.81.226:8000/docs` |

## 🆘 常用命令

```bash
docker-compose ps                    # 查看状态
docker-compose logs -f api           # 查看日志
docker-compose restart               # 重启服务
curl http://localhost:8000/health    # 测试 API
```

## 📚 文档

- **DEPLOYMENT-SOLUTION-SUMMARY.md** - 完整解决方案
- **QUICK-DEPLOYMENT-FIX.md** - 快速修复
- **DEPLOYMENT-TROUBLESHOOTING.md** - 故障排查

---

**就这么简单！立即开始部署！** 🚀
