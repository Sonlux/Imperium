# Imperium IBN Framework - Disaster Recovery Procedures

## Overview

This document outlines procedures for recovering the Imperium Intent-Based Networking framework from various failure scenarios.

## Backup Strategy

### Automated Backups
- **Daily**: Full database and configuration backup at 2:00 AM
- **Location**: `/home/imperium/Imperium/backups/`
- **Retention**: 7 days (configurable via `RETENTION_DAYS`)
- **Cron job**: `/etc/cron.d/imperium`

### Manual Backup
```bash
cd /home/imperium/Imperium
./scripts/backup.sh
```

### Backup Contents
- SQLite database (`data/imperium.db`)
- Configuration files (`config/*.yaml`, `config/*.conf`)
- Environment file (`.env`)
- Monitoring configuration (`monitoring/`)

## Recovery Scenarios

### Scenario 1: Service Crash

**Symptoms**: API not responding, systemd service failed

**Recovery Steps**:
```bash
# Check service status
sudo systemctl status imperium

# View logs for errors
sudo journalctl -u imperium -n 50

# Restart service
sudo systemctl restart imperium

# Verify recovery
curl http://localhost:5000/health
```

### Scenario 2: Database Corruption

**Symptoms**: API errors, database integrity failures

**Recovery Steps**:
```bash
# Stop service
sudo systemctl stop imperium

# Check database integrity
sqlite3 data/imperium.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
LATEST_BACKUP=$(ls -t backups/*.tar.gz | head -1)
tar -xzf "$LATEST_BACKUP" -C /tmp
cp /tmp/imperium_backup_*/imperium.db data/imperium.db

# Start service
sudo systemctl start imperium
```

### Scenario 3: Docker Services Down

**Symptoms**: MQTT, Prometheus, or Grafana unavailable

**Recovery Steps**:
```bash
# Check container status
docker ps -a

# Restart all services
docker compose down
docker compose up -d

# Verify services
docker compose ps
curl http://localhost:1883  # MQTT
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
```

### Scenario 4: Network Enforcement Failure

**Symptoms**: Traffic control rules not applied

**Recovery Steps**:
```bash
# Check tc status
tc qdisc show dev eth0

# Clear all rules
sudo tc qdisc del dev eth0 root 2>/dev/null

# Restart service to reapply policies
sudo systemctl restart imperium

# Verify tc rules
tc -s qdisc show dev eth0
```

### Scenario 5: Complete System Recovery

**For full system restore after catastrophic failure**:

```bash
# 1. Install fresh Raspberry Pi OS (64-bit)

# 2. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv docker.io git

# 3. Clone repository
git clone https://github.com/Sonlux/Imperium.git
cd Imperium

# 4. Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Restore from backup (if available)
# Copy backup file to Pi, then:
tar -xzf imperium_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp
cp /tmp/imperium_backup_*/imperium.db data/
cp /tmp/imperium_backup_*/config/.env .env
cp /tmp/imperium_backup_*/config/*.yaml config/

# 6. Start services
docker compose up -d
sudo cp config/imperium.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable imperium
sudo systemctl start imperium

# 7. Verify
curl http://localhost:5000/health
```

## Health Monitoring

### Automated Health Check
Uncomment the health check line in `/etc/cron.d/imperium` to enable automatic service restart on failure.

### Manual Health Check
```bash
./scripts/recovery_test.sh
```

### Key Endpoints to Monitor
| Service | URL | Expected |
|---------|-----|----------|
| API | http://localhost:5000/health | `{"status":"healthy"}` |
| MQTT | localhost:1883 | Connection accepted |
| Prometheus | http://localhost:9090/-/ready | ready |
| Grafana | http://localhost:3000/api/health | `{"database":"ok"}` |

## Log Locations

| Component | Log Location |
|-----------|-------------|
| Imperium API | `/var/log/imperium/app.log` |
| Systemd | `journalctl -u imperium` |
| Docker | `docker logs <container>` |
| MQTT | `docker logs imperium-mqtt` |

## Contact & Escalation

- **Repository**: https://github.com/Sonlux/Imperium
- **Branch**: ibn-initial-integration
- **Documentation**: [SECURITY.md](SECURITY.md), [README.md](../README.md)

## Maintenance Schedule

| Task | Frequency | Time |
|------|-----------|------|
| Database backup | Daily | 2:00 AM |
| Log cleanup | Weekly | Sunday 3:00 AM |
| Database vacuum | Monthly | 1st at 4:00 AM |
| System updates | Manual | As needed |

---

**Last Updated**: 2026-01-21  
**Version**: 1.0
