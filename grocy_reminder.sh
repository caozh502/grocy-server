#!/bin/bash
# 从 grocy-server 目录加载 .env
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export $(grep -v '^\s*#' "$SCRIPT_DIR/.env" | grep -v '^\s*$' | xargs)

DB_PATH="${DB_PATH:-$HOME/grocy-data/data/grocy.db}"

EXPIRED=$(sqlite3 "$DB_PATH" "
SELECT p.name, s.best_before_date
FROM stock s JOIN products p ON p.id = s.product_id
WHERE s.best_before_date < date('now') AND s.open = 0 AND s.amount > 0
ORDER BY s.best_before_date ASC
")

REMINDER=$(sqlite3 "$DB_PATH" "
SELECT p.name, s.best_before_date, s.amount
FROM stock s JOIN products p ON p.id = s.product_id
WHERE s.best_before_date BETWEEN date('now') AND date('now', '+3 days')
  AND s.open = 0
ORDER BY s.best_before_date ASC
")

TODAY=$(date +%Y-%m-%d)
MSG="📋 *Grocy 食品日报* · $TODAY%0A%0A"

if [ -n "$EXPIRED" ]; then
  COUNT=$(echo "$EXPIRED" | wc -l)
  MSG+="🔴 *已过期: $COUNT 件*%0A"
  while IFS='|' read -r name date; do
    MSG+="  • $name（$date）%0A"
  done <<< "$EXPIRED"
  MSG+="%0A"
fi

if [ -n "$REMINDER" ]; then
  MSG+="⚠️ *未来3天到期：*%0A"
  while IFS='|' read -r name date amount; do
    DAYS_LEFT=$(( ( $(date -d "$date" +%s) - $(date +%s) ) / 86400 ))
    if [ "$DAYS_LEFT" -le 1 ]; then EMOJI="🔴"; elif [ "$DAYS_LEFT" -le 2 ]; then EMOJI="🟡"; else EMOJI="🟢"; fi
    MSG+="${EMOJI} $name — $date（剩${DAYS_LEFT}天）%0A"
  done <<< "$REMINDER"
else
  MSG+="✅ 未来3天没有食品到期"
fi

curl -s "https://api.telegram.org/bot$BOT_TOKEN/sendMessage?chat_id=$GROUP_ID&text=$MSG&parse_mode=Markdown" > /dev/null
