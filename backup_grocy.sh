#!/bin/bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR=~/grocy-backups
TMP_DIR=$BACKUP_DIR/tmp-$TIMESTAMP
mkdir -p $TMP_DIR

cd ~ && docker compose stop grocy

cp -r ~/grocy-data/data $TMP_DIR/grocy-core
cp ~/grocy-server/docker-compose.yml $TMP_DIR/
cp ~/grocy-server/Caddyfile $TMP_DIR/
cp ~/grocy-server/backup_grocy.sh $TMP_DIR/
cp ~/grocy-server/grocy_reminder.sh $TMP_DIR/
cp ~/grocy-server/grocy_bot.py $TMP_DIR/
cp ~/.config/rclone/rclone.conf $TMP_DIR/
crontab -l > $TMP_DIR/crontab-ubuntu.txt 2>/dev/null || true
sudo crontab -l > $TMP_DIR/crontab-root.txt 2>/dev/null || true

docker compose start grocy

tar -czf $BACKUP_DIR/grocy-full-$TIMESTAMP.tar.gz -C $TMP_DIR/ .
rm -rf $TMP_DIR

sleep 3
rclone copy $BACKUP_DIR/grocy-full-$TIMESTAMP.tar.gz gdrive:grocy-backups/ || echo "⚠️ Upload failed"

ls -t $BACKUP_DIR/grocy-full-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo "✅ Full backup done: grocy-full-$TIMESTAMP.tar.gz"
