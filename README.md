# Grocy 食品管理系统

## 🗂️ 仓库结构

```
grocy-server/
├── grocy_bot.py          ← Telegram Bot（从 .env 读取配置）
├── grocy_reminder.sh     ← 每日到期提醒（早上8点）
├── backup_grocy.sh       ← Google Drive 全量备份（凌晨3点）
├── docker-compose.yml    ← Docker 服务定义
├── Caddyfile             ← 域名 + HTTPS 配置
├── .env                  ← 环境变量（不入库，见 .env.example）
├── .github/workflows/deploy.yml  ← 自动部署
└── README.md
```

## 🔧 日常开发流程

```
本地 VS Code 改代码 → git push
                      ↓
         GitHub Actions 自动触发
                      ↓
         SSH 进 VPS → git pull → 重启 Bot
                      ↓
                 ✅ 1分钟内生效
```

## 📌 服务器信息

| 项目 | 值 |
|------|-----|
| VPS IP | 132.226.82.250 |
| 域名 | https://calebhomelist.duckdns.org |
| Grocy | admin / admin |
| Telegram 群组 | -1003852773059 |
| Google Drive 备份 | grocy-backups/ |

## 🤖 Telegram Bot 命令

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

## 💾 定时任务

| 时间 | 任务 | 位置 |
|------|------|------|
| 03:00 每天 | 全量备份到 Google Drive | `backup_grocy.sh` |
| 08:00 每天 | Telegram 到期提醒 | `grocy_reminder.sh` |

## ⚡ 恢复步骤

1. 新 VPS 安装 Docker + rclone + sqlite3
2. `rclone copy gdrive:grocy-backups/ ~/grocy-restore/` 下载最新备份
3. `git clone git@github.com:caozh502/grocy-server.git`
4. 配置 `.env`（参考 `.env.example`）
5. `docker compose up -d` 启动
6. `nohup python3 grocy_bot.py &` 启动 Bot

详细恢复流程见桌面 `GROCY_RECOVERY_README.md`
