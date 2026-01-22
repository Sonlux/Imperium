#!/usr/bin/env python3
"""
Secure Secret Generator for Imperium IBN Framework

This script generates cryptographically secure secrets for:
- API_SECRET_KEY
- JWT_SECRET_KEY
- GRAFANA_ADMIN_PASSWORD
- MQTT_PASSWORD
- POSTGRES_PASSWORD

Usage:
    python scripts/generate_secrets.py           # Interactive mode
    python scripts/generate_secrets.py --auto    # Auto-generate all
    python scripts/generate_secrets.py --key api # Generate specific key
"""

import secrets
import string
import argparse
import sys
from pathlib import Path


def generate_api_secret(length=32):
    """Generate API secret key (hex format)"""
    return secrets.token_hex(length)


def generate_jwt_secret(length=32):
    """Generate JWT secret key (hex format)"""
    return secrets.token_hex(length)


def generate_password(length=24, special_chars=True):
    """
    Generate strong password with mixed characters
    
    Args:
        length: Password length (minimum 16)
        special_chars: Include special characters
    
    Returns:
        Secure random password
    """
    if length < 16:
        raise ValueError("Password must be at least 16 characters")
    
    alphabet = string.ascii_letters + string.digits
    if special_chars:
        alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure password has at least one of each type
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
            if not special_chars or any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                return password


def update_env_file(key, value, env_path=".env"):
    """
    Update .env file with new secret
    
    Args:
        key: Environment variable name
        value: New secret value
        env_path: Path to .env file
    """
    env_file = Path(env_path)
    
    if not env_file.exists():
        print(f"⚠️  {env_path} not found. Create from .env.example first:")
        print(f"    cp .env.example {env_path}")
        return False
    
    # Read existing content
    lines = env_file.read_text().splitlines()
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)
    
    # If key not found, append it
    if not updated:
        new_lines.append(f"{key}={value}")
    
    # Write back
    env_file.write_text('\n'.join(new_lines) + '\n')
    return True


def interactive_mode():
    """Interactive secret generation wizard"""
    print("=" * 70)
    print("🔐 Imperium Secret Generator - Interactive Mode")
    print("=" * 70)
    print()
    
    secrets_to_generate = []
    
    # Ask which secrets to generate
    print("Select secrets to generate (y/n):")
    print()
    
    if input("  Generate API_SECRET_KEY? [y/N]: ").lower().startswith('y'):
        secrets_to_generate.append(('API_SECRET_KEY', 'api'))
    
    if input("  Generate JWT_SECRET_KEY? [y/N]: ").lower().startswith('y'):
        secrets_to_generate.append(('JWT_SECRET_KEY', 'jwt'))
    
    if input("  Generate GRAFANA_ADMIN_PASSWORD? [y/N]: ").lower().startswith('y'):
        secrets_to_generate.append(('GRAFANA_ADMIN_PASSWORD', 'password'))
    
    if input("  Generate MQTT_PASSWORD? [y/N]: ").lower().startswith('y'):
        secrets_to_generate.append(('MQTT_PASSWORD', 'password'))
    
    if input("  Generate POSTGRES_PASSWORD? [y/N]: ").lower().startswith('y'):
        secrets_to_generate.append(('POSTGRES_PASSWORD', 'password'))
    
    if not secrets_to_generate:
        print("\nNo secrets selected. Exiting.")
        return
    
    print()
    print("=" * 70)
    print("Generated Secrets:")
    print("=" * 70)
    print()
    
    # Generate secrets
    results = {}
    for key, secret_type in secrets_to_generate:
        if secret_type == 'api':
            value = generate_api_secret()
        elif secret_type == 'jwt':
            value = generate_jwt_secret()
        elif secret_type == 'password':
            value = generate_password()
        else:
            value = secrets.token_hex(16)
        
        results[key] = value
        print(f"{key}:")
        print(f"  {value}")
        print()
    
    # Ask if user wants to update .env
    print("=" * 70)
    update = input("\nUpdate .env file with these secrets? [y/N]: ")
    
    if update.lower().startswith('y'):
        success_count = 0
        for key, value in results.items():
            if update_env_file(key, value):
                success_count += 1
        
        if success_count == len(results):
            print(f"\n✅ Successfully updated {success_count} secrets in .env")
            print("⚠️  IMPORTANT: Never commit .env to version control!")
        else:
            print(f"\n⚠️  Updated {success_count}/{len(results)} secrets")
    else:
        print("\n📋 Copy the secrets above to your .env file manually")
    
    print()


def auto_mode():
    """Automatically generate all secrets"""
    print("=" * 70)
    print("🔐 Imperium Secret Generator - Auto Mode")
    print("=" * 70)
    print()
    
    secrets_map = {
        'API_SECRET_KEY': generate_api_secret(),
        'JWT_SECRET_KEY': generate_jwt_secret(),
        'GRAFANA_ADMIN_PASSWORD': generate_password(24),
        'MQTT_PASSWORD': generate_password(20, special_chars=False),
        'POSTGRES_PASSWORD': generate_password(24),
    }
    
    print("Generated Secrets:")
    print("-" * 70)
    for key, value in secrets_map.items():
        print(f"{key}={value}")
    print()
    
    # Update .env file
    success_count = 0
    for key, value in secrets_map.items():
        if update_env_file(key, value):
            success_count += 1
    
    if success_count == len(secrets_map):
        print(f"✅ Successfully updated all {success_count} secrets in .env")
        print("⚠️  IMPORTANT: Never commit .env to version control!")
    else:
        print(f"⚠️  Updated {success_count}/{len(secrets_map)} secrets")
    
    print()


def single_key_mode(key_type):
    """Generate a single specific key"""
    key_map = {
        'api': ('API_SECRET_KEY', generate_api_secret),
        'jwt': ('JWT_SECRET_KEY', generate_jwt_secret),
        'grafana': ('GRAFANA_ADMIN_PASSWORD', lambda: generate_password(24)),
        'mqtt': ('MQTT_PASSWORD', lambda: generate_password(20, special_chars=False)),
        'postgres': ('POSTGRES_PASSWORD', lambda: generate_password(24)),
    }
    
    if key_type not in key_map:
        print(f"❌ Unknown key type: {key_type}")
        print(f"   Valid types: {', '.join(key_map.keys())}")
        sys.exit(1)
    
    key_name, generator = key_map[key_type]
    value = generator()
    
    print(f"{key_name}={value}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate cryptographically secure secrets for Imperium',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_secrets.py              # Interactive mode
  python scripts/generate_secrets.py --auto       # Auto-generate all
  python scripts/generate_secrets.py --key api    # Generate API secret
  python scripts/generate_secrets.py --key jwt    # Generate JWT secret

Valid key types: api, jwt, grafana, mqtt, postgres
        """
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Automatically generate all secrets and update .env'
    )
    
    parser.add_argument(
        '--key',
        type=str,
        help='Generate specific key type (api, jwt, grafana, mqtt, postgres)'
    )
    
    args = parser.parse_args()
    
    # Check if .env.example exists
    if not Path('.env.example').exists():
        print("❌ .env.example not found in current directory")
        print("   Run this script from the project root directory")
        sys.exit(1)
    
    # Check if .env exists
    if not Path('.env').exists() and (args.auto or args.key):
        print("⚠️  .env file not found. Creating from .env.example...")
        Path('.env').write_text(Path('.env.example').read_text())
        print("✅ Created .env from template")
        print()
    
    # Execute based on mode
    if args.key:
        single_key_mode(args.key)
    elif args.auto:
        auto_mode()
    else:
        interactive_mode()


if __name__ == '__main__':
    main()
