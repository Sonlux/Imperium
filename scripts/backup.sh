#!/bin/bash
# Imperium IBN Framework - Backup Script
# Backs up database, configs, and logs

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/home/imperium/Imperium/backups}"
IMPERIUM_DIR="${IMPERIUM_DIR:-/home/imperium/Imperium}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="imperium_backup_${DATE}"
RETENTION_DAYS=${RETENTION_DAYS:-7}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Imperium Backup Script ===${NC}"
echo "Backup directory: $BACKUP_DIR"
echo "Date: $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# 1. Backup SQLite database
echo -e "\n${YELLOW}[1/4] Backing up database...${NC}"
if [ -f "$IMPERIUM_DIR/data/imperium.db" ]; then
    sqlite3 "$IMPERIUM_DIR/data/imperium.db" ".backup '$BACKUP_DIR/$BACKUP_NAME/imperium.db'"
    echo -e "${GREEN}✓ Database backed up${NC}"
else
    echo -e "${RED}✗ Database not found${NC}"
fi

# 2. Backup configuration files
echo -e "\n${YELLOW}[2/4] Backing up configuration...${NC}"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME/config"
cp -r "$IMPERIUM_DIR/config/"*.yaml "$BACKUP_DIR/$BACKUP_NAME/config/" 2>/dev/null || true
cp -r "$IMPERIUM_DIR/config/"*.conf "$BACKUP_DIR/$BACKUP_NAME/config/" 2>/dev/null || true
cp "$IMPERIUM_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME/config/.env" 2>/dev/null || true
echo -e "${GREEN}✓ Configuration backed up${NC}"

# 3. Backup Prometheus data (optional - can be large)
echo -e "\n${YELLOW}[3/4] Backing up monitoring config...${NC}"
mkdir -p "$BACKUP_DIR/$BACKUP_NAME/monitoring"
cp "$IMPERIUM_DIR/monitoring/prometheus/prometheus.yml" "$BACKUP_DIR/$BACKUP_NAME/monitoring/" 2>/dev/null || true
cp -r "$IMPERIUM_DIR/monitoring/grafana/provisioning" "$BACKUP_DIR/$BACKUP_NAME/monitoring/" 2>/dev/null || true
echo -e "${GREEN}✓ Monitoring config backed up${NC}"

# 4. Create compressed archive
echo -e "\n${YELLOW}[4/4] Creating archive...${NC}"
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"
echo -e "${GREEN}✓ Archive created: ${BACKUP_NAME}.tar.gz${NC}"

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
echo -e "\nBackup size: $BACKUP_SIZE"

# 5. Clean old backups (retention policy)
echo -e "\n${YELLOW}Cleaning backups older than $RETENTION_DAYS days...${NC}"
find "$BACKUP_DIR" -name "imperium_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
REMAINING=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Retained $REMAINING backup(s)${NC}"

# Summary
echo -e "\n${GREEN}=== Backup Complete ===${NC}"
echo "Location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "Size: $BACKUP_SIZE"

# Restore instructions
echo -e "\n${YELLOW}To restore:${NC}"
echo "  tar -xzf $BACKUP_DIR/${BACKUP_NAME}.tar.gz -C /tmp"
echo "  cp /tmp/$BACKUP_NAME/imperium.db $IMPERIUM_DIR/data/"
echo "  cp /tmp/$BACKUP_NAME/config/* $IMPERIUM_DIR/config/"
