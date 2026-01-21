#!/bin/bash
# Imperium IBN Framework - Recovery Script
# Tests system recovery from crash scenarios

set -e

IMPERIUM_DIR="${IMPERIUM_DIR:-/home/imperium/Imperium}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Imperium Recovery Test Script ===${NC}"

# Test 1: Service recovery
echo -e "\n${YELLOW}[Test 1] Service Recovery Test${NC}"
echo "Stopping imperium service..."
sudo systemctl stop imperium 2>/dev/null || echo "Service not running"
sleep 2
echo "Starting imperium service..."
sudo systemctl start imperium
sleep 5
STATUS=$(systemctl is-active imperium 2>/dev/null || echo "inactive")
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}✓ Service recovered successfully${NC}"
else
    echo -e "${RED}✗ Service failed to recover${NC}"
    exit 1
fi

# Test 2: API health check
echo -e "\n${YELLOW}[Test 2] API Health Check${NC}"
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null || echo '{"status":"error"}')
    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✓ API is healthy (attempt $((RETRY_COUNT + 1)))${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for API... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ API health check failed after $MAX_RETRIES attempts${NC}"
fi

# Test 3: Docker services recovery
echo -e "\n${YELLOW}[Test 3] Docker Services Recovery${NC}"
cd "$IMPERIUM_DIR"
docker compose restart mqtt prometheus grafana 2>/dev/null
sleep 5
MQTT_STATUS=$(docker inspect -f '{{.State.Running}}' imperium-mqtt 2>/dev/null || echo "false")
if [ "$MQTT_STATUS" = "true" ]; then
    echo -e "${GREEN}✓ MQTT broker recovered${NC}"
else
    echo -e "${RED}✗ MQTT broker failed${NC}"
fi

# Test 4: Database integrity check
echo -e "\n${YELLOW}[Test 4] Database Integrity Check${NC}"
if [ -f "$IMPERIUM_DIR/data/imperium.db" ]; then
    INTEGRITY=$(sqlite3 "$IMPERIUM_DIR/data/imperium.db" "PRAGMA integrity_check;" 2>/dev/null)
    if [ "$INTEGRITY" = "ok" ]; then
        echo -e "${GREEN}✓ Database integrity OK${NC}"
    else
        echo -e "${RED}✗ Database integrity check failed${NC}"
    fi
else
    echo -e "${RED}✗ Database not found${NC}"
fi

# Test 5: Network interface check
echo -e "\n${YELLOW}[Test 5] Network Interface Check${NC}"
if ip link show eth0 &>/dev/null; then
    echo -e "${GREEN}✓ Network interface eth0 available${NC}"
else
    echo -e "${YELLOW}⚠ eth0 not available, checking wlan0...${NC}"
    if ip link show wlan0 &>/dev/null; then
        echo -e "${GREEN}✓ Network interface wlan0 available${NC}"
    fi
fi

# Summary
echo -e "\n${GREEN}=== Recovery Test Complete ===${NC}"
echo "All critical systems tested for recovery capability"
