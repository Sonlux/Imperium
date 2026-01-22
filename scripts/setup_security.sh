#!/bin/bash
# Quick Security Setup Script for Imperium IBN Framework
# Run this BEFORE first deployment to production

set -e  # Exit on error

echo "======================================================================"
echo "🔐 Imperium Security Setup Wizard"
echo "======================================================================"
echo ""

# Check if running from project root
if [ ! -f ".env.example" ]; then
    echo "❌ Error: .env.example not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

# Step 1: Create .env from template
echo "Step 1: Environment Configuration"
echo "----------------------------------------------------------------------"
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists"
    read -p "   Overwrite with template? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✅ Created new .env from template"
    else
        echo "⏭️  Keeping existing .env file"
    fi
else
    cp .env.example .env
    echo "✅ Created .env from template"
fi
echo ""

# Step 2: Generate secrets
echo "Step 2: Generate Secrets"
echo "----------------------------------------------------------------------"
echo "Generating cryptographically secure secrets..."
echo ""

# Generate secrets using Python
python3 << 'PYTHON_SCRIPT'
import secrets
import os
from pathlib import Path

# Generate secrets
api_secret = secrets.token_hex(32)
jwt_secret = secrets.token_hex(32)
grafana_password = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()') for _ in range(24))

# Read .env
env_file = Path('.env')
content = env_file.read_text()

# Replace placeholder secrets
content = content.replace('GENERATE_RANDOM_SECRET_KEY_HERE', api_secret)
content = content.replace('GENERATE_RANDOM_JWT_SECRET_KEY_HERE', jwt_secret)
content = content.replace('CHANGE_ME_TO_STRONG_PASSWORD', grafana_password)

# Write back
env_file.write_text(content)

print(f"✅ Generated API_SECRET_KEY ({len(api_secret)} chars)")
print(f"✅ Generated JWT_SECRET_KEY ({len(jwt_secret)} chars)")
print(f"✅ Generated GRAFANA_ADMIN_PASSWORD ({len(grafana_password)} chars)")
PYTHON_SCRIPT

echo ""

# Step 3: Set file permissions
echo "Step 3: Secure File Permissions"
echo "----------------------------------------------------------------------"
chmod 600 .env
echo "✅ Set .env permissions to 600 (owner read/write only)"

if [ -f "data/imperium.db" ]; then
    chmod 600 data/imperium.db
    echo "✅ Set database permissions to 600"
fi

if [ -d "backups" ]; then
    chmod 700 backups
    chmod 600 backups/*.tar.gz 2>/dev/null || true
    echo "✅ Set backup directory permissions to 700"
fi
echo ""

# Step 4: Verify .gitignore
echo "Step 4: Verify Git Configuration"
echo "----------------------------------------------------------------------"
if git check-ignore .env >/dev/null 2>&1; then
    echo "✅ .env is properly excluded from git"
else
    echo "⚠️  WARNING: .env may not be excluded from git!"
    echo "   Verify .gitignore contains: .env"
fi

if git ls-files | grep -q "^.env$"; then
    echo "❌ CRITICAL: .env is tracked by git!"
    echo "   Run: git rm --cached .env"
    echo "   Then commit the removal"
else
    echo "✅ .env is not tracked by git"
fi
echo ""

# Step 5: Display summary
echo "======================================================================"
echo "✅ Security Setup Complete!"
echo "======================================================================"
echo ""
echo "Next Steps:"
echo "1. Review .env file and customize settings if needed"
echo "2. Set MQTT_USERNAME and MQTT_PASSWORD in .env"
echo "3. Update NETWORK_INTERFACE in .env (default: eth0)"
echo "4. For production, enable TLS for MQTT (see SECURITY.md)"
echo "5. Review SECURITY_CHECKLIST.md for full hardening guide"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - NEVER commit .env to version control"
echo "   - Change default passwords on first login"
echo "   - Enable firewall (ufw) on production systems"
echo "   - Rotate secrets quarterly or after incidents"
echo ""
echo "Your generated Grafana admin password is in .env"
echo "Access Grafana at: http://localhost:3000"
echo "  Username: admin"
echo "  Password: (check GRAFANA_ADMIN_PASSWORD in .env)"
echo ""
echo "======================================================================"
