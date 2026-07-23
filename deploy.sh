#!/bin/bash
# 部署脚本：从 .env 读取配置，生成 Caddyfile 等，重启服务
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 加载 .env
export $(grep -v '^\s*#' .env | grep -v '^\s*$' | xargs)

echo "⏳ Generating Caddyfile..."
cat > Caddyfile << CADDYEOF
# Auto-generated from .env - do not edit directly
${DOMAIN:-your-domain.duckdns.org} {
    reverse_proxy grocy:80
}
CADDYEOF

echo "⏳ Copying Caddyfile to home..."
cp Caddyfile ~/Caddyfile

echo "⏳ Restarting bot..."
sudo systemctl restart grocy-bot

echo "✅ Deploy complete"
