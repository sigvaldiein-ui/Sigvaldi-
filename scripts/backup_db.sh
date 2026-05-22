#!/bin/bash
DB="/workspace/Sigvaldi-/state_store.db"
BACKUP="/workspace/Sigvaldi-/backups/state_store_$(date +%Y%m%d_%H%M%S).db"
mkdir -p /workspace/Sigvaldi-/backups
sqlite3 "$DB" ".backup '$BACKUP'"
echo "✅ Backup: $BACKUP"
