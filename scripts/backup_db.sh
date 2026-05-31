#!/bin/bash
DB="/workspace/Sigvaldi-/state_store.db"
BACKUP_DIR="/workspace/Sigvaldi-/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/state_store_$(date +%Y%m%d_%H%M%S).db"
sqlite3 "$DB" ".backup '$BACKUP_FILE'" 2>/dev/null && echo "✅ Backup: $BACKUP_FILE" || echo "❌ Backup failed"
ls -la "$BACKUP_FILE" 2>/dev/null
# Hreinsa gömlu afrit (geyma aðeins 48 klst)
find "$BACKUP_DIR" -name "state_store_*.db" -mtime +2 -delete 2>/dev/null
