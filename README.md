# Grocy Server

家庭食品库存管理系统 — Grocy + Telegram Bot + 自动备份。

## 🗂️ 仓库结构

```
grocy-server/
├── grocy_bot.py          ← Telegram Bot（从 .env 读取配置）
├── grocy_reminder.sh     ← 每日到期提醒
├── backup_grocy.sh       ← Google Drive 全量备份
├── docker-compose.yml    ← Docker 服务定义
├── Caddyfile             ← 域名 + HTTPS 配置
├── .env                  ← 环境变量（不入库，见 .env.example）
├── .github/workflows/deploy.yml  ← 自动部署
└── README.md
```

## 🔧 功能

| 功能 | 说明 |
|------|------|
| 📦 食品库存管理 | Grocy Web 界面，扫码入库 |
| 🤖 Telegram Bot | 群组命令查询库存、到期提醒 |
| 💾 自动备份 | 每天凌晨 3:00 全量备份到 Google Drive |
| 🚀 自动部署 | GitHub Actions 自动推送代码到 VPS |

## 🤖 Bot 命令

| 命令 | 功能 |
|------|------|
| `/help` | 显示所有命令 |
| `/check` | 未来3天到期食品 |
| `/stock` | 全部库存 |
| `/search <词>` | 搜索食品 |
| `/expired` | 已过期食品 |
| `/soon <N>` | 未来N天到期 |
| `/stats` | 库存统计 |
| `/add <名称>,<到期日>,<数量>` | 快速添加（到期日可省略=永不过期） |

## 🚀 自动部署

```
本地改代码 → git push
              ↓
  GitHub Actions 自动触发
              ↓
  SSH 进 VPS → git pull → systemctl restart grocy-bot
              ↓
         ✅ 30秒内生效
```

## ⚡ 快速开始

### 前提

- 一台 Linux VPS（Ubuntu 22.04+）
- Docker + Docker Compose
- Telegram Bot Token（通过 @BotFather 创建）

### 部署

```bash
# 1. 克隆仓库
git clone git@github.com:caozh502/grocy-server.git
cd grocy-server

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 Token、群组 ID、域名、VPS IP

# 3. 启动 Grocy + Caddy
docker compose up -d

# 4. 安装 Python 依赖 & 启动 Bot
pip install python-telegram-bot
sudo cp grocy-bot.service /etc/systemd/system/
sudo systemctl enable --now grocy-bot

# 5. 配置定时备份和提醒
crontab crontab.example
```

## ⚙️ 环境变量说明

参考 `.env.example`，所有敏感信息均从 `.env` 读取，此文件不提交到仓库。

## 🔑 GitHub Secrets（自动部署需要）

| Secret | 说明 |
|--------|------|
| `VPS_HOST` | 服务器 IP |
| `VPS_USER` | SSH 用户名 |
| `VPS_SSH_KEY` | SSH 私钥 |
