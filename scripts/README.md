# Scripts Directory

This directory contains utility scripts for managing the Imperium IBN Framework.

## 🔐 Security Scripts

### generate_secrets.py

**Purpose:** Generate cryptographically secure secrets for production deployment.

**Features:**

- Interactive wizard mode
- Automatic generation of all secrets
- Single key generation
- Direct `.env` file updates
- Uses Python `secrets` module (cryptographically secure)

**Usage:**

```bash
# Interactive mode (recommended for first-time setup)
python scripts/generate_secrets.py

# Auto-generate all secrets and update .env
python scripts/generate_secrets.py --auto

# Generate specific secret
python scripts/generate_secrets.py --key api      # API_SECRET_KEY
python scripts/generate_secrets.py --key jwt      # JWT_SECRET_KEY
python scripts/generate_secrets.py --key grafana  # GRAFANA_ADMIN_PASSWORD
python scripts/generate_secrets.py --key mqtt     # MQTT_PASSWORD
python scripts/generate_secrets.py --key postgres # POSTGRES_PASSWORD
```

**Output Example:**

```
API_SECRET_KEY=a1b2c3d4e5f6...64chars...
JWT_SECRET_KEY=f6e5d4c3b2a1...64chars...
GRAFANA_ADMIN_PASSWORD=Xy9$mK2...24chars...
```

**Security Notes:**

- Uses `secrets.token_hex()` for keys (32 bytes entropy = 64 hex chars)
- Uses `secrets.choice()` for passwords (24+ chars mixed)
- Automatically updates `.env` file with proper permissions
- Validates secret strength before writing

---

### setup_security.sh (Linux/Mac)

**Purpose:** One-command security setup for production deployment.

**What it does:**

1. ✅ Creates `.env` from `.env.example` (if not exists)
2. ✅ Generates all secrets using Python
3. ✅ Sets file permissions (`chmod 600 .env`)
4. ✅ Secures database and backups
5. ✅ Verifies git configuration
6. ✅ Displays next steps

**Usage:**

```bash
# Run from project root
bash scripts/setup_security.sh

# Or make executable first
chmod +x scripts/setup_security.sh
./scripts/setup_security.sh
```

**Output:**

```
======================================================================
🔐 Imperium Security Setup Wizard
======================================================================

Step 1: Environment Configuration
----------------------------------------------------------------------
✅ Created .env from template

Step 2: Generate Secrets
----------------------------------------------------------------------
✅ Generated API_SECRET_KEY (64 chars)
✅ Generated JWT_SECRET_KEY (64 chars)
✅ Generated GRAFANA_ADMIN_PASSWORD (24 chars)

Step 3: Secure File Permissions
----------------------------------------------------------------------
✅ Set .env permissions to 600 (owner read/write only)
✅ Set database permissions to 600
✅ Set backup directory permissions to 700

Step 4: Verify Git Configuration
----------------------------------------------------------------------
✅ .env is properly excluded from git
✅ .env is not tracked by git

======================================================================
✅ Security Setup Complete!
======================================================================
```

**When to use:**

- ✅ First-time production deployment on Raspberry Pi
- ✅ After cloning repository to new server
- ✅ When rotating all secrets (emergency or scheduled)
- ✅ Setting up development environment with proper security

---

### setup_security.ps1 (Windows)

**Purpose:** Windows PowerShell version of security setup script.

**What it does:**

- Same as `setup_security.sh` but for Windows
- PowerShell-native commands
- Color-coded output
- Works on Windows development machines

**Usage:**

```powershell
# Run from project root (PowerShell)
.\scripts\setup_security.ps1

# If execution policy prevents running:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_security.ps1
```

**When to use:**

- ✅ Setting up development environment on Windows
- ✅ Testing security configuration before Pi deployment
- ✅ Generating secrets on Windows for remote deployment

---

## 🔧 Utility Scripts

### backup.sh

**Purpose:** Create encrypted backup of database and configuration.

**Usage:**

```bash
bash scripts/backup.sh
```

**Output:** `backups/imperium_backup_YYYYMMDD_HHMMSS.tar.gz`

**Includes:**

- `data/imperium.db` (SQLite database)
- `config/*.yaml` (configuration files)
- `.env.example` (template, NOT actual .env)

**Automated:** Runs daily at 2:00 AM via cron (see crontab)

---

### restore.sh

**Purpose:** Restore from backup.

**Usage:**

```bash
# List available backups
bash scripts/restore.sh --list

# Restore from specific backup
bash scripts/restore.sh backups/imperium_backup_20260121_151354.tar.gz

# Restore latest backup
bash scripts/restore.sh --latest
```

**Safety:** Creates backup of current state before restoring

---

### rotate_secrets.sh

**Purpose:** Rotate all secrets (quarterly maintenance).

**Usage:**

```bash
# Rotate all secrets
bash scripts/rotate_secrets.sh

# Test mode (don't restart services)
bash scripts/rotate_secrets.sh --dry-run
```

**What it does:**

1. ✅ Backs up current `.env`
2. ✅ Generates new secrets
3. ✅ Updates `.env` file
4. ✅ Restarts services (imperium, docker)
5. ✅ Verifies services operational
6. ✅ Logs rotation to audit trail

**Schedule:** Run every 90 days (add to calendar)

---

## 📦 Deployment Scripts

### deploy_pi.sh

**Purpose:** Deploy/update Imperium on Raspberry Pi.

**Usage:**

```bash
# Deploy to Pi (from development machine)
bash scripts/deploy_pi.sh pi@raspberrypi.local

# Deploy with specific branch
bash scripts/deploy_pi.sh pi@raspberrypi.local --branch production
```

**What it does:**

1. ✅ SSH into Pi
2. ✅ Pull latest code from git
3. ✅ Update dependencies
4. ✅ Restart services
5. ✅ Run health checks
6. ✅ Display status

---

### health_check.sh

**Purpose:** Verify all services are operational.

**Usage:**

```bash
bash scripts/health_check.sh
```

**Checks:**

- ✅ Imperium API (port 5000)
- ✅ MQTT broker (port 1883)
- ✅ Prometheus (port 9090)
- ✅ Grafana (port 3000)
- ✅ Database connectivity
- ✅ IoT node count
- ✅ Disk space
- ✅ CPU/memory usage

**Output:**

```
======================================================================
Imperium IBN Health Check
======================================================================

[✓] API Service         : HEALTHY (200 OK)
[✓] MQTT Broker         : CONNECTED
[✓] Prometheus          : HEALTHY (10 targets)
[✓] Grafana             : HEALTHY (200 OK)
[✓] Database            : CONNECTED (49KB, 4 tables)
[✓] IoT Nodes           : 10 ACTIVE
[✓] Disk Space          : 42% used (46GB free)
[✓] CPU Usage           : 55%
[✓] Memory Usage        : 39% (3.0GB/7.6GB)

Overall Status: ✅ ALL SYSTEMS OPERATIONAL
```

---

## 🧪 Testing Scripts

### test_api.sh

**Purpose:** Test all API endpoints.

**Usage:**

```bash
# Test local API
bash scripts/test_api.sh

# Test remote API
bash scripts/test_api.sh http://raspberrypi.local:5000
```

**Tests:**

- ✅ Health endpoint (`/api/health`)
- ✅ Authentication (`/api/auth/login`)
- ✅ Intent submission (`/api/intents`)
- ✅ Policy retrieval (`/api/policies`)
- ✅ Rate limiting
- ✅ JWT token validation

---

### test_mqtt.sh

**Purpose:** Test MQTT broker connectivity.

**Usage:**

```bash
bash scripts/test_mqtt.sh
```

**Tests:**

- ✅ Broker connection
- ✅ Publish message
- ✅ Subscribe to topic
- ✅ Message delivery
- ✅ QoS levels

---

## 🔄 Maintenance Scripts

### cleanup.sh

**Purpose:** Clean temporary files, old logs, and backups.

**Usage:**

```bash
# Dry run (show what would be deleted)
bash scripts/cleanup.sh --dry-run

# Actually clean
bash scripts/cleanup.sh

# Aggressive clean (removes more)
bash scripts/cleanup.sh --aggressive
```

**Removes:**

- ✅ Old log files (>7 days)
- ✅ Old backups (>30 days)
- ✅ Python cache files
- ✅ Temporary files
- ✅ Docker unused volumes (if --aggressive)

---

### update_deps.sh

**Purpose:** Update Python dependencies safely.

**Usage:**

```bash
bash scripts/update_deps.sh
```

**What it does:**

1. ✅ Creates backup of current environment
2. ✅ Updates pip, setuptools, wheel
3. ✅ Updates all packages in requirements.txt
4. ✅ Runs tests to verify compatibility
5. ✅ Rolls back if tests fail

---

## 📚 Quick Reference

### Security Setup Workflow

```bash
# 1. Clone repository
git clone https://github.com/Sonlux/Imperium.git
cd Imperium

# 2. Run security setup (Linux/Mac)
bash scripts/setup_security.sh

# OR (Windows)
.\scripts\setup_security.ps1

# 3. Verify configuration
cat .env | grep "SECRET_KEY"  # Should show generated keys

# 4. Check file permissions (Linux)
ls -la .env                    # Should be -rw------- (600)

# 5. Verify git protection
git check-ignore .env          # Should output: .env
```

### Secret Rotation Workflow

```bash
# 1. Generate new secrets
python scripts/generate_secrets.py --auto

# 2. Restart services
sudo systemctl restart imperium
docker compose restart

# 3. Verify services
bash scripts/health_check.sh

# 4. Test API authentication
bash scripts/test_api.sh

# 5. Log rotation
echo "$(date): Secrets rotated" >> logs/security_audit.log
```

### Deployment Workflow

```bash
# 1. Run health check before deployment
bash scripts/health_check.sh

# 2. Create backup
bash scripts/backup.sh

# 3. Deploy to Pi
bash scripts/deploy_pi.sh pi@raspberrypi.local

# 4. Verify deployment
bash scripts/health_check.sh
bash scripts/test_api.sh http://raspberrypi.local:5000
```

---

## 🚨 Emergency Procedures

### If Secrets Compromised

```bash
# 1. IMMEDIATELY rotate secrets
python scripts/generate_secrets.py --auto

# 2. IMMEDIATELY restart services
sudo systemctl restart imperium
docker compose restart

# 3. Review access logs
grep "401\|403\|429" logs/imperium.log | tail -n 50

# 4. Notify stakeholders
bash scripts/send_alert.sh "SECURITY INCIDENT: Secrets compromised"

# 5. Document incident
cat >> logs/security_incidents.log << EOF
Date: $(date)
Incident: Secret compromise
Action: Emergency rotation completed
EOF
```

### If Service Down

```bash
# 1. Check service status
sudo systemctl status imperium
docker compose ps

# 2. Check logs
tail -f logs/imperium.log
docker compose logs -f

# 3. Restart services
sudo systemctl restart imperium
docker compose restart

# 4. Verify recovery
bash scripts/health_check.sh

# 5. If still down, restore from backup
bash scripts/restore.sh --latest
```

---

## 📝 Script Development Guidelines

When creating new scripts for this directory:

1. **Naming:** Use lowercase with underscores (`my_script.sh`)
2. **Shebang:** Include proper shebang (`#!/bin/bash` or `#!/usr/bin/env python3`)
3. **Help:** Add `--help` flag with usage information
4. **Dry-run:** Support `--dry-run` flag for safe testing
5. **Logging:** Log actions to `logs/scripts.log`
6. **Error handling:** Use `set -e` in bash, proper try/catch in Python
7. **Permissions:** Make executable (`chmod +x scripts/my_script.sh`)
8. **Documentation:** Add entry to this README
9. **Testing:** Test on both development and production environments

---

## 🔗 Related Documentation

- [SECURITY_CHECKLIST.md](../SECURITY_CHECKLIST.md) - Pre-deployment security verification
- [SECURITY_IMPLEMENTATION.md](../docs/SECURITY_IMPLEMENTATION.md) - Security implementation summary
- [DISASTER_RECOVERY.md](../docs/DISASTER_RECOVERY.md) - Backup and recovery procedures
- [RASPBERRY_PI_SETUP.md](../docs/RASPBERRY_PI_SETUP.md) - Production deployment guide

---

**Last Updated:** 2026-01-21  
**Version:** 1.0  
**Maintainer:** Imperium Development Team
