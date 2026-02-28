# Security & Production Features

This document describes the security enhancements and production-ready features added to Imperium.

## 🔐 Authentication System

### Overview

JWT (JSON Web Token) based authentication system with user management and role-based access control.

### Features

- **User Registration**: Create new user accounts with username/password
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: User and admin roles with different permissions
- **Password Hashing**: bcrypt for secure password storage
- **Token Expiry**: Configurable token lifetime (default: 24 hours)

### API Endpoints

#### Register New User

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password",
  "email": "john@example.com"
}
```

#### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

#### Verify Token

```bash
GET /api/v1/auth/verify
Authorization: Bearer <token>
```

#### Get User Profile

```bash
GET /api/v1/auth/profile
Authorization: Bearer <token>
```

### Using Authentication

#### Protected Endpoints

Add authentication headers to requests:

```bash
curl -X POST http://localhost:5000/api/v1/intents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Prioritize sensor data"}'
```

#### PowerShell Example

```powershell
# Login
$loginData = @{
    username = "admin"
    password = "admin"
} | ConvertTo-Json

$response = Invoke-RestMethod -Method POST `
    -Uri "http://localhost:5000/api/v1/auth/login" `
    -Body $loginData `
    -ContentType "application/json"

$token = $response.token

# Use token for requests
$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Method GET `
    -Uri "http://localhost:5000/api/v1/intents" `
    -Headers $headers
```

### Default Admin Account

- **Username**: `admin`
- **Password**: `admin`
- **⚠️ IMPORTANT**: Change this password immediately in production!

```bash
# Initialize database with default admin
python scripts/init_database.py
```

---

## 🚦 Rate Limiting

### Overview

In-memory rate limiter to protect API endpoints from abuse and ensure fair resource usage.

### Configuration

Default limits:

- **General endpoints**: 100 requests/hour
- **Authentication endpoints**: 10 requests/hour
- **Intent submission**: 50 requests/hour
- **Privileged users**: 200 requests/hour

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 2024-01-15T14:30:00Z
```

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Try again after 2024-01-15T14:30:00Z",
  "retry_after": "2024-01-15T14:30:00Z"
}
```

Status Code: `429 Too Many Requests`

### IP Whitelisting

Bypass rate limits for trusted IPs:

```python
from src.rate_limiter import IPWhitelist

ip_whitelist = IPWhitelist()
ip_whitelist.add("192.168.1.100")
ip_whitelist.add("10.0.0.5")
```

### Statistics

Get rate limiting statistics:

```python
from src.rate_limiter import RateLimiter

rate_limiter = RateLimiter()
stats = rate_limiter.get_stats()

# Returns:
# {
#   "total_clients": 15,
#   "active_clients": 8,
#   "clients": [...]
# }
```

---

## 💾 Persistent Storage

### Overview

SQLite database for persistent storage of intents, policies, metrics, and user accounts.

### Database Schema

#### Intents Table

```sql
CREATE TABLE intents (
    id VARCHAR(36) PRIMARY KEY,
    original_intent TEXT NOT NULL,
    parsed_intent TEXT,  -- JSON string
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Policies Table

```sql
CREATE TABLE policies (
    id VARCHAR(36) PRIMARY KEY,
    intent_id VARCHAR(36) REFERENCES intents(id),
    type VARCHAR(50) NOT NULL,
    parameters TEXT,  -- JSON string
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    enforced_at DATETIME
);
```

#### Metrics History Table

```sql
CREATE TABLE metrics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    device_id VARCHAR(50),
    intent_id VARCHAR(36),
    metadata TEXT  -- JSON string
);
```

#### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

### Database Operations

#### Initialize Database

```bash
python scripts/init_database.py
```

#### Using Database Manager

```python
from src.database import DatabaseManager

db = DatabaseManager(db_path='data/imperium.db')

# Add intent
db.add_intent(
    intent_id='intent-001',
    original_intent='Prioritize sensor data',
    parsed_intent={'priority': 'high'},
    status='active'
)

# Query intents
intents = db.get_all_intents(limit=50)

# Add metrics
db.add_metric(
    metric_name='latency_ms',
    metric_value=45.2,
    device_id='sensor-001',
    intent_id='intent-001'
)
```

### Backup & Recovery

#### Backup Database

```bash
# Simple backup
cp data/imperium.db data/backups/imperium-$(date +%Y%m%d-%H%M%S).db

# With compression
tar -czf data/backups/imperium-$(date +%Y%m%d).tar.gz data/imperium.db
```

#### Restore Database

```bash
# Restore from backup
cp data/backups/imperium-20240115.db data/imperium.db

# Restore from compressed backup
tar -xzf data/backups/imperium-20240115.tar.gz -C data/
```

---

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# JWT Configuration
export JWT_SECRET_KEY="your-super-secret-key-change-this"

# Database
export DATABASE_PATH="data/imperium.db"

# API Configuration
export API_HOST="0.0.0.0"
export API_PORT="5000"
export FLASK_ENV="production"

# Rate Limiting
export RATE_LIMIT_ENABLED="true"
export RATE_LIMIT_DEFAULT="100"  # requests per hour
```

### .env File Example

```env
# Security
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_TOKEN_EXPIRY_HOURS=24

# Database
DATABASE_PATH=data/imperium.db

# API
API_HOST=0.0.0.0
API_PORT=5000
FLASK_ENV=production

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_AUTH=10
RATE_LIMIT_INTENTS=50

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883

# Network
NETWORK_INTERFACE=eth0
```

---

## 🚀 Deployment

### Development (Windows)

1. **Initialize Database**

   ```bash
   python scripts/init_database.py
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start Services**

   ```bash
   docker-compose up -d
   ```

4. **Run Controller**

   ```bash
   python src/main.py
   ```

5. **Test Authentication**
   ```powershell
   .\scripts\test_api_with_auth.ps1
   ```

### Production (Raspberry Pi)

1. **Setup Systemd Service**

   ```bash
   sudo cp config/imperium.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable imperium.service
   ```

2. **Create Log Directory**

   ```bash
   sudo mkdir -p /var/log/imperium
   sudo chown pi:pi /var/log/imperium
   ```

3. **Secure JWT Secret**

   ```bash
   # Generate secure secret
   python -c "import secrets; print(secrets.token_hex(32))"

   # Update service file
   sudo nano /etc/systemd/system/imperium.service
   # Set JWT_SECRET_KEY=<generated-secret>
   ```

4. **Start Service**

   ```bash
   sudo systemctl start imperium.service
   sudo systemctl status imperium.service
   ```

5. **View Logs**
   ```bash
   sudo journalctl -u imperium.service -f
   tail -f /var/log/imperium/controller.log
   ```

---

## 🔒 Security Best Practices

### 1. Change Default Credentials

```bash
# Login as admin
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# TODO: Implement password change endpoint
```

### 2. Use Strong JWT Secret

```bash
# Generate cryptographically secure secret
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env
echo "JWT_SECRET_KEY=<generated-secret>" >> .env
```

### 3. Enable HTTPS (Production)

```bash
# Use reverse proxy (nginx) with SSL
sudo apt install nginx certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot --nginx -d imperium.yourdomain.com
```

### 4. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5000/tcp  # API (or 443 for HTTPS)
sudo ufw enable
```

### 5. Regular Backups

```bash
# Add to crontab
0 2 * * * /home/pi/Imperium/scripts/backup_database.sh
```

---

## 📊 Monitoring

### Authentication Events

Monitor authentication activity:

```python
# Log failed login attempts
logger.warning(f"Failed login attempt for user: {username}")

# Monitor token generation
logger.info(f"Token generated for user: {username}")
```

### Rate Limit Statistics

```bash
# Check rate limit stats via API
curl http://localhost:5000/api/v1/admin/rate-limits \
  -H "Authorization: Bearer <admin-token>"
```

### Database Metrics

```python
# Monitor database size
import os
db_size = os.path.getsize('data/imperium.db') / (1024 * 1024)  # MB
print(f"Database size: {db_size:.2f} MB")

# Count records
intents_count = len(db.get_all_intents())
policies_count = len(db.get_all_policies())
```

---

## 🧪 Testing

### Run Test Suite

```bash
# All tests
python -m pytest tests/

# Authentication tests only
python -m pytest tests/test_auth.py -v

# Rate limiter tests
python -m pytest tests/test_rate_limiter.py -v

# Database tests
python -m pytest tests/test_database.py -v
```

### Manual Testing

```powershell
# Run comprehensive test script
.\scripts\test_api_with_auth.ps1

# Test specific features
.\scripts\test_authentication.ps1
.\scripts\test_rate_limiting.ps1
```

---

## 📚 Additional Resources

- [JWT.io](https://jwt.io/) - JWT debugging and documentation
- [bcrypt](https://github.com/pyca/bcrypt/) - Password hashing library
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM documentation
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/) - Flask security best practices

---

## ⚠️ Known Limitations (Windows Development)

1. **tc/iptables enforcement**: Simulated on Windows, real enforcement requires Linux
2. **systemd service**: Only applicable on Linux systems
3. **File permissions**: Windows ACLs differ from Linux permissions

**Note**: All security features (authentication, rate limiting, database) work fully on Windows for development and testing.
