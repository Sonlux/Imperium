# Security Checklist - Imperium IBN Framework

## Pre-Deployment Security Verification

This checklist MUST be completed before deploying to production.

## 🔴 CRITICAL - Before First Deployment

### Environment Configuration

- [ ] **Copy .env.example to .env**

  ```bash
  cp .env.example .env
  ```

- [ ] **Generate API Secret Key**

  ```bash
  python -c "import secrets; print('API_SECRET_KEY=' + secrets.token_hex(32))" >> .env
  ```

- [ ] **Generate JWT Secret Key**

  ```bash
  python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))" >> .env
  ```

- [ ] **Set Strong Grafana Password**
  - Minimum 16 characters
  - Mix of uppercase, lowercase, numbers, symbols
  - Update in .env: `GRAFANA_ADMIN_PASSWORD=<strong-password>`

- [ ] **Configure MQTT Credentials**
  - Set `MQTT_USERNAME` and `MQTT_PASSWORD`
  - Minimum 12 characters for MQTT password

- [ ] **Verify Production Settings**
  ```bash
  # Ensure these are set correctly in .env:
  API_DEBUG=false
  DEBUG=false
  JWT_ENABLED=true
  RATE_LIMIT_ENABLED=true
  ENFORCEMENT_DRY_RUN=false  # false for real enforcement
  ```

### File Protection

- [ ] **Verify .gitignore Configuration**

  ```bash
  # Check .env is NOT tracked by git:
  git check-ignore .env
  # Should output: .env

  # Check database is NOT tracked:
  git check-ignore data/imperium.db
  # Should output: data/imperium.db

  # Check backups are NOT tracked:
  git check-ignore backups/*.tar.gz
  # Should output: backups/*.tar.gz
  ```

- [ ] **Remove .env from Git History (if accidentally committed)**

  ```bash
  # WARNING: This rewrites git history
  git filter-branch --force --index-filter \
    "git rm --cached --ignore-unmatch .env" \
    --prune-empty --tag-name-filter cat -- --all

  # Force push (coordinate with team first)
  git push origin --force --all
  git push origin --force --tags
  ```

- [ ] **Set Proper File Permissions (Linux/Raspberry Pi)**

  ```bash
  # Protect .env file
  chmod 600 .env

  # Protect database
  chmod 600 data/imperium.db

  # Protect backups
  chmod 700 backups/
  chmod 600 backups/*.tar.gz

  # Verify ownership
  ls -la .env data/imperium.db backups/
  ```

## 🟡 IMPORTANT - Network Security

### MQTT Broker Security

- [ ] **Enable TLS/SSL for MQTT**

  ```bash
  # Generate certificates (or use Let's Encrypt)
  openssl req -x509 -newkey rsa:4096 -keyout mqtt-key.pem \
    -out mqtt-cert.pem -days 365 -nodes \
    -subj "/CN=raspberrypi.local"

  # Move to secure location
  sudo mkdir -p /etc/mosquitto/certs
  sudo mv mqtt-*.pem /etc/mosquitto/certs/
  sudo chmod 600 /etc/mosquitto/certs/*.pem
  ```

- [ ] **Update .env for TLS**

  ```bash
  MQTT_USE_TLS=true
  MQTT_CA_CERT_PATH=/etc/mosquitto/certs/mqtt-cert.pem
  MQTT_CLIENT_CERT_PATH=/etc/mosquitto/certs/mqtt-cert.pem
  MQTT_CLIENT_KEY_PATH=/etc/mosquitto/certs/mqtt-key.pem
  ```

- [ ] **Configure Mosquitto for Authentication**

  ```bash
  # Edit /etc/mosquitto/mosquitto.conf:
  sudo nano /etc/mosquitto/mosquitto.conf

  # Add:
  allow_anonymous false
  password_file /etc/mosquitto/passwd

  # Create password file:
  sudo mosquitto_passwd -c /etc/mosquitto/passwd imperium
  sudo systemctl restart mosquitto
  ```

### Firewall Configuration

- [ ] **Enable UFW Firewall (Linux)**

  ```bash
  sudo ufw enable

  # Allow SSH (IMPORTANT - do this first!)
  sudo ufw allow 22/tcp

  # Allow API
  sudo ufw allow 5000/tcp

  # Allow Prometheus (if needed externally)
  sudo ufw allow 9090/tcp

  # Allow Grafana
  sudo ufw allow 3000/tcp

  # Allow MQTT (internal only)
  sudo ufw allow from 127.0.0.1 to any port 1883

  # Deny all other incoming
  sudo ufw default deny incoming
  sudo ufw default allow outgoing

  # Check status
  sudo ufw status verbose
  ```

- [ ] **Configure API CORS Restrictions**

  ```bash
  # In .env, set specific origins (not *):
  API_CORS_ORIGINS=http://localhost:3000,http://raspberrypi.local:3000

  # Set allowed hosts:
  ALLOWED_HOSTS=localhost,127.0.0.1,raspberrypi.local,<your-pi-ip>
  ```

### SSH Hardening (Raspberry Pi)

- [ ] **Disable Password Authentication**

  ```bash
  # Generate SSH key on your PC:
  ssh-keygen -t ed25519 -C "imperium@raspberrypi"

  # Copy to Pi:
  ssh-copy-id pi@raspberrypi.local

  # Edit SSH config:
  sudo nano /etc/ssh/sshd_config

  # Set:
  PasswordAuthentication no
  PermitRootLogin no
  PubkeyAuthentication yes

  # Restart SSH:
  sudo systemctl restart ssh
  ```

## 🟢 RECOMMENDED - Additional Security

### Database Security

- [ ] **Enable Database Encryption (PostgreSQL)**

  ```bash
  # If using PostgreSQL instead of SQLite:
  # Update .env:
  DATABASE_TYPE=postgresql
  DATABASE_URL=postgresql+psycopg2://imperium:<password>@localhost/imperium?sslmode=require

  # Configure PostgreSQL SSL:
  sudo nano /etc/postgresql/*/main/postgresql.conf
  # Set: ssl = on
  ```

- [ ] **Regular Database Backups**

  ```bash
  # Automated via cron (already configured):
  crontab -l | grep backup

  # Manual backup:
  ./scripts/backup.sh

  # Verify backup exists:
  ls -lh backups/
  ```

- [ ] **Backup Encryption**

  ```bash
  # Install gpg:
  sudo apt-get install gnupg

  # Encrypt backup:
  gpg --symmetric --cipher-algo AES256 backups/imperium_backup_*.tar.gz

  # Store encrypted version securely, delete unencrypted:
  rm backups/imperium_backup_*.tar.gz
  ```

### Monitoring & Alerts

- [ ] **Configure Grafana Alerts**
  - Set up email/webhook notifications
  - Alert on CPU > 80%
  - Alert on memory > 90%
  - Alert on policy enforcement failures
  - Alert on MQTT connection loss

- [ ] **Enable Prometheus Authentication**
  ```bash
  # Edit prometheus.yml:
  basic_auth:
    username: prometheus
    password: <hashed-password>
  ```

### Secret Rotation

- [ ] **Schedule Secret Rotation**

  ```bash
  # Add to calendar/documentation:
  # - Rotate JWT_SECRET_KEY every 90 days
  # - Rotate API_SECRET_KEY every 90 days
  # - Rotate MQTT credentials every 180 days
  # - Rotate Grafana admin password every 180 days
  ```

- [ ] **Document Secret Rotation Process**
  ```bash
  # See SECURITY.md section "Secret Rotation"
  # OR create scripts/rotate_secrets.sh
  ```

### Logging & Audit

- [ ] **Enable Detailed Logging**

  ```bash
  # In .env:
  LOG_LEVEL=INFO  # Use DEBUG only for troubleshooting
  LOG_FILE=logs/imperium.log
  ```

- [ ] **Set Up Log Monitoring**

  ```bash
  # Install logwatch or fail2ban:
  sudo apt-get install logwatch fail2ban

  # Configure fail2ban for API rate limiting:
  sudo nano /etc/fail2ban/jail.local
  # Add custom rules for 429 status codes
  ```

- [ ] **Secure Log Files**

  ```bash
  # Restrict log access:
  chmod 700 logs/
  chmod 600 logs/*.log

  # Set up log rotation (already configured):
  ls -la /etc/logrotate.d/imperium
  ```

## 🔵 VERIFICATION - Post-Deployment Checks

### Secret Verification

- [ ] **Verify No Secrets in Git**

  ```bash
  # Search for common secret patterns:
  git grep -i "api_secret_key.*="
  git grep -i "jwt_secret_key.*="
  git grep -i "password.*="

  # Should return NO results from .env files
  ```

- [ ] **Check Secret Strength**
  ```bash
  # Verify secret lengths:
  grep API_SECRET_KEY .env | wc -c  # Should be > 70
  grep JWT_SECRET_KEY .env | wc -c  # Should be > 70
  ```

### Network Verification

- [ ] **Test MQTT Connection**

  ```bash
  # From external machine:
  mosquitto_sub -h raspberrypi.local -p 1883 -t "test" \
    -u imperium -P <password>

  # Should connect successfully or reject without credentials
  ```

- [ ] **Test API Authentication**

  ```bash
  # Test without token (should fail):
  curl http://raspberrypi.local:5000/api/intents
  # Expected: 401 Unauthorized

  # Test with token (should succeed):
  TOKEN=$(curl -X POST http://raspberrypi.local:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"<your-password>"}' | jq -r '.token')

  curl -H "Authorization: Bearer $TOKEN" http://raspberrypi.local:5000/api/intents
  # Expected: 200 OK
  ```

- [ ] **Test Rate Limiting**

  ```bash
  # Rapid fire 100 requests:
  for i in {1..100}; do curl http://raspberrypi.local:5000/api/health & done

  # Should eventually return: 429 Too Many Requests
  ```

### File Permission Verification

- [ ] **Check Critical File Permissions**

  ```bash
  # .env file:
  stat -c "%a %n" .env  # Should be 600

  # Database:
  stat -c "%a %n" data/imperium.db  # Should be 600

  # Backups:
  stat -c "%a %n" backups/  # Should be 700
  ```

## 🔴 INCIDENT RESPONSE

### If Secrets Are Compromised

1. **Immediately rotate all secrets:**

   ```bash
   # Generate new secrets:
   python -c "import secrets; print(secrets.token_hex(32))" > new_api_secret.txt
   python -c "import secrets; print(secrets.token_hex(32))" > new_jwt_secret.txt

   # Update .env with new secrets
   # Restart service:
   sudo systemctl restart imperium
   ```

2. **Revoke all existing JWT tokens:**

   ```bash
   # Changing JWT_SECRET_KEY invalidates all tokens
   # Users must re-authenticate
   ```

3. **Check access logs:**

   ```bash
   grep "401\|403\|429" logs/imperium.log
   tail -f logs/imperium.log
   ```

4. **Notify stakeholders:**
   - Document the incident
   - Inform users to change passwords
   - Review and update security procedures

### If .env Was Committed to Git

1. **Remove from current commit:**

   ```bash
   git rm --cached .env
   git commit -m "Remove accidentally committed .env"
   ```

2. **Remove from git history** (see File Protection section above)

3. **Rotate ALL secrets immediately**

4. **Force push to remote** (coordinate with team)

## 📋 Compliance Checklist

For academic/production compliance:

- [ ] All secrets generated using cryptographically secure random functions
- [ ] No hardcoded credentials in source code
- [ ] All sensitive files excluded from version control
- [ ] TLS/SSL enabled for all network communications
- [ ] Authentication required for all API endpoints
- [ ] Rate limiting enabled to prevent abuse
- [ ] Logging configured for security auditing
- [ ] Regular backups scheduled and tested
- [ ] Firewall configured with least-privilege rules
- [ ] SSH hardened with key-only authentication
- [ ] Database access restricted to localhost
- [ ] Monitoring alerts configured for security events

## 🔄 Ongoing Maintenance

### Weekly

- [ ] Review access logs for suspicious activity
- [ ] Check for failed authentication attempts
- [ ] Verify backup creation and integrity

### Monthly

- [ ] Update all dependencies: `pip install -U -r requirements.txt`
- [ ] Review and rotate development secrets
- [ ] Check disk space for logs/backups

### Quarterly

- [ ] Rotate production secrets (API, JWT, passwords)
- [ ] Security audit with latest vulnerability scanners
- [ ] Update TLS/SSL certificates if needed
- [ ] Review and update firewall rules

### Annually

- [ ] Full security audit and penetration testing
- [ ] Review and update security documentation
- [ ] Update disaster recovery procedures
- [ ] Compliance certification renewal (if applicable)

---

**Last Updated:** 2026-01-21  
**Version:** 1.0  
**Owner:** Imperium Security Team
