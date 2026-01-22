# Quick Security Setup for Windows (PowerShell)
# Run this BEFORE first deployment to production

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🔐 Imperium Security Setup Wizard (Windows)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running from project root
if (-not (Test-Path ".env.example")) {
    Write-Host "❌ Error: .env.example not found" -ForegroundColor Red
    Write-Host "   Please run this script from the project root directory"
    exit 1
}

# Step 1: Create .env from template
Write-Host "Step 1: Environment Configuration" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "   Overwrite with template? [y/N]"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Copy-Item ".env.example" ".env" -Force
        Write-Host "✅ Created new .env from template" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Keeping existing .env file" -ForegroundColor Blue
    }
} else {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env from template" -ForegroundColor Green
}
Write-Host ""

# Step 2: Generate secrets
Write-Host "Step 2: Generate Secrets" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"
Write-Host "Generating cryptographically secure secrets..."
Write-Host ""

# Generate secrets using Python
python -c @"
import secrets
import string
from pathlib import Path

# Generate secrets
api_secret = secrets.token_hex(32)
jwt_secret = secrets.token_hex(32)

# Generate password with mixed characters
alphabet = string.ascii_letters + string.digits + '!@#$%^&*()'
grafana_password = ''.join(secrets.choice(alphabet) for _ in range(24))

# Read .env
env_file = Path('.env')
content = env_file.read_text()

# Replace placeholder secrets
content = content.replace('GENERATE_RANDOM_SECRET_KEY_HERE', api_secret)
content = content.replace('GENERATE_RANDOM_JWT_SECRET_KEY_HERE', jwt_secret)
content = content.replace('CHANGE_ME_TO_STRONG_PASSWORD', grafana_password)

# Write back
env_file.write_text(content)

print(f'✅ Generated API_SECRET_KEY ({len(api_secret)} chars)')
print(f'✅ Generated JWT_SECRET_KEY ({len(jwt_secret)} chars)')
print(f'✅ Generated GRAFANA_ADMIN_PASSWORD ({len(grafana_password)} chars)')
"@

Write-Host ""

# Step 3: Verify .gitignore
Write-Host "Step 3: Verify Git Configuration" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

$gitIgnoreCheck = git check-ignore .env 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ .env is properly excluded from git" -ForegroundColor Green
} else {
    Write-Host "⚠️  WARNING: .env may not be excluded from git!" -ForegroundColor Yellow
    Write-Host "   Verify .gitignore contains: .env"
}

$gitTracked = git ls-files | Select-String -Pattern "^.env$"
if ($gitTracked) {
    Write-Host "❌ CRITICAL: .env is tracked by git!" -ForegroundColor Red
    Write-Host "   Run: git rm --cached .env" -ForegroundColor Red
    Write-Host "   Then commit the removal"
} else {
    Write-Host "✅ .env is not tracked by git" -ForegroundColor Green
}
Write-Host ""

# Step 4: Display summary
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "✅ Security Setup Complete!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review .env file and customize settings if needed"
Write-Host "2. Set MQTT_USERNAME and MQTT_PASSWORD in .env"
Write-Host "3. Update NETWORK_INTERFACE in .env (Windows: simulation mode)"
Write-Host "4. For production on Raspberry Pi, enable TLS (see SECURITY.md)"
Write-Host "5. Review SECURITY_CHECKLIST.md for full hardening guide"
Write-Host ""
Write-Host "⚠️  IMPORTANT:" -ForegroundColor Red
Write-Host "   - NEVER commit .env to version control"
Write-Host "   - Change default passwords on first login"
Write-Host "   - Rotate secrets quarterly or after incidents"
Write-Host ""
Write-Host "Your generated Grafana admin password is in .env"
Write-Host "Access Grafana at: http://localhost:3000"
Write-Host "  Username: admin"
Write-Host "  Password: (check GRAFANA_ADMIN_PASSWORD in .env)"
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
