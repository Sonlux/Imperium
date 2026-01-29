# Product Requirements Document (PRD)
# Imperium CLI - Command Line Interface

**Document Version:** 1.0  
**Date:** 2026-01-23  
**Author:** Imperium Team  
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Objectives](#3-goals--objectives)
4. [User Personas](#4-user-personas)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [CLI Command Structure](#7-cli-command-structure)
8. [User Stories](#8-user-stories)
9. [Technical Architecture](#9-technical-architecture)
10. [UI/UX Design](#10-uiux-design)
11. [Security Considerations](#11-security-considerations)
12. [Success Metrics](#12-success-metrics)
13. [Implementation Phases](#13-implementation-phases)
14. [Dependencies & Risks](#14-dependencies--risks)
15. [Appendix](#15-appendix)

---

## 1. Executive Summary

### 1.1 Overview
The Imperium CLI is a command-line interface tool that provides users with an intuitive, efficient way to interact with the Imperium Intent-Based Networking (IBN) framework. It replaces manual `curl` commands and hardcoded terminal inputs with a streamlined, user-friendly command structure.

### 1.2 Value Proposition
- **Reduce Time-to-Action:** Submit intents in seconds instead of constructing complex API calls
- **Improve User Experience:** Auto-completion, help text, and interactive prompts
- **Increase Adoption:** Lower barrier to entry for network administrators
- **Enhance Productivity:** Batch operations, scripting support, and output formatting

### 1.3 Target Release
- **MVP (Phase 1):** Q1 2026
- **Full Release (Phase 2):** Q2 2026

---

## 2. Problem Statement

### 2.1 Current Challenges

| Challenge | Impact | Severity |
|-----------|--------|----------|
| Manual curl commands are error-prone | Users make syntax mistakes | High |
| JWT tokens must be managed manually | Authentication friction | High |
| No command history or auto-completion | Slow workflow | Medium |
| JSON output is hard to read | Poor user experience | Medium |
| No batch operations | Time-consuming for bulk tasks | Medium |
| Requires API knowledge | Steep learning curve | High |

### 2.2 Current Workflow (Pain Points)

```bash
# Step 1: Login and extract token (complex)
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Step 2: Submit intent (verbose)
curl -s -X POST http://localhost:5000/api/v1/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"prioritize temperature sensors"}' | python3 -m json.tool

# Step 3: Check status (repeat for each query)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/intents | python3 -m json.tool
```

### 2.3 Desired Workflow (With CLI)

```bash
# Step 1: Login (one-time, token cached)
imperium login

# Step 2: Submit intent (simple)
imperium intent submit "prioritize temperature sensors"

# Step 3: Check status
imperium intent list
```

---

## 3. Goals & Objectives

### 3.1 Primary Goals

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| **G1** | Simplify intent submission | Submit intent in single command |
| **G2** | Automate authentication | Token caching and auto-refresh |
| **G3** | Improve output readability | Formatted tables, JSON, YAML options |
| **G4** | Enable scripting | Non-interactive mode with exit codes |
| **G5** | Reduce errors | Input validation and helpful messages |

### 3.2 Key Results (OKRs)

- **KR1:** Reduce average time to submit intent from 45s to 5s
- **KR2:** Achieve 90% user satisfaction in usability surveys
- **KR3:** Support 100% of API functionality via CLI
- **KR4:** Zero authentication-related support tickets after launch

### 3.3 Non-Goals (Out of Scope for MVP)

- GUI/Web interface
- Mobile application
- Real-time streaming logs
- Plugin/extension system

---

## 4. User Personas

### 4.1 Primary Persona: Network Administrator

**Name:** Alex Chen  
**Role:** Senior Network Administrator  
**Technical Level:** Advanced  
**Goals:**
- Quickly configure network policies
- Monitor system health
- Automate repetitive tasks

**Pain Points:**
- Dislikes constructing JSON payloads
- Wants quick feedback on policy status
- Needs to integrate with existing scripts

**Quote:** *"I want to type what I need and have it just work."*

### 4.2 Secondary Persona: DevOps Engineer

**Name:** Sam Rodriguez  
**Role:** DevOps/SRE  
**Technical Level:** Expert  
**Goals:**
- Automate IBN deployment
- Integrate with CI/CD pipelines
- Monitor system metrics

**Pain Points:**
- Needs programmatic access
- Requires consistent exit codes
- Wants machine-readable output

**Quote:** *"I need to script everything and trust the exit codes."*

### 4.3 Tertiary Persona: IoT Developer

**Name:** Jordan Lee  
**Role:** IoT Solutions Developer  
**Technical Level:** Intermediate  
**Goals:**
- Test device policies quickly
- Debug connectivity issues
- Prototype intent configurations

**Pain Points:**
- Unfamiliar with networking terminology
- Needs examples and templates
- Wants interactive guidance

**Quote:** *"Show me examples and let me modify them."*

---

## 5. Functional Requirements

### 5.1 Authentication Module

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-AUTH-01 | Login with username/password | P0 | Must have |
| FR-AUTH-02 | Secure token storage (~/.imperium/credentials) | P0 | Encrypted |
| FR-AUTH-03 | Auto-refresh expired tokens | P0 | Seamless UX |
| FR-AUTH-04 | Logout and clear credentials | P1 | Security |
| FR-AUTH-05 | Support API key authentication | P2 | For CI/CD |
| FR-AUTH-06 | MFA support (TOTP) | P3 | Future |

### 5.2 Intent Management Module

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-INT-01 | Submit intent via natural language | P0 | Core feature |
| FR-INT-02 | List all intents | P0 | With pagination |
| FR-INT-03 | Get intent by ID | P0 | Detailed view |
| FR-INT-04 | Delete/deactivate intent | P1 | Soft delete |
| FR-INT-05 | Update intent description | P2 | Modify existing |
| FR-INT-06 | Import intents from file (JSON/YAML) | P1 | Batch operations |
| FR-INT-07 | Export intents to file | P1 | Backup/share |
| FR-INT-08 | Intent templates | P2 | Predefined examples |

### 5.3 Policy Management Module

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-POL-01 | List all policies | P0 | With filters |
| FR-POL-02 | Get policy by ID | P0 | Show TC commands |
| FR-POL-03 | Apply policy manually | P1 | Override auto-apply |
| FR-POL-04 | Rollback policy | P1 | Undo changes |
| FR-POL-05 | Policy diff (before/after) | P2 | Change tracking |
| FR-POL-06 | Export policies | P1 | Documentation |

### 5.4 Network Enforcement Module

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-NET-01 | Show current TC rules | P0 | Status check |
| FR-NET-02 | Show traffic statistics | P0 | Bandwidth/packets |
| FR-NET-03 | Clear all TC rules | P1 | Reset network |
| FR-NET-04 | Test network config (dry-run) | P1 | Preview changes |
| FR-NET-05 | Apply TC rules from file | P2 | Manual override |

### 5.5 Monitoring Module

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-MON-01 | Health check | P0 | System status |
| FR-MON-02 | Service status (Docker/systemd) | P0 | Quick view |
| FR-MON-03 | Query Prometheus metrics | P1 | CLI metrics |
| FR-MON-04 | Show IoT node status | P1 | Device list |
| FR-MON-05 | Export metrics to file | P2 | Reporting |

### 5.6 Configuration Module

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-CFG-01 | Set API endpoint URL | P0 | Multi-environment |
| FR-CFG-02 | Set output format (table/json/yaml) | P0 | User preference |
| FR-CFG-03 | Set verbosity level | P1 | Debug mode |
| FR-CFG-04 | Profile management (dev/prod) | P2 | Environment switching |
| FR-CFG-05 | Configuration file support | P1 | ~/.imperium/config |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PERF-01 | Command startup time | < 200ms |
| NFR-PERF-02 | API response rendering | < 100ms |
| NFR-PERF-03 | Memory footprint | < 50MB |
| NFR-PERF-04 | Support 1000+ items in list commands | Without pagination lag |

### 6.2 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-REL-01 | Graceful error handling | 100% of API errors |
| NFR-REL-02 | Network timeout handling | Configurable (default 30s) |
| NFR-REL-03 | Retry logic for transient failures | 3 retries with backoff |

### 6.3 Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-USE-01 | Help text for every command | 100% coverage |
| NFR-USE-02 | Tab auto-completion | Bash, Zsh, Fish |
| NFR-USE-03 | Color-coded output | Errors red, success green |
| NFR-USE-04 | Progress indicators | For long operations |

### 6.4 Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SEC-01 | Credentials encrypted at rest | AES-256 |
| NFR-SEC-02 | No credentials in command history | Use stdin for passwords |
| NFR-SEC-03 | Secure TLS connections | TLS 1.2+ |
| NFR-SEC-04 | Audit logging | Optional verbose mode |

### 6.5 Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-COM-01 | Linux support | Ubuntu 20.04+, Debian 11+, RHEL 8+ |
| NFR-COM-02 | macOS support | 11.0+ (Big Sur) |
| NFR-COM-03 | Windows support | WSL2, PowerShell (P2) |
| NFR-COM-04 | Python version | 3.9+ |
| NFR-COM-05 | ARM64 support | Raspberry Pi 4 |

---

## 7. CLI Command Structure

### 7.1 Command Hierarchy

```
imperium
├── login                    # Authenticate with API
├── logout                   # Clear credentials
├── config                   # Configuration management
│   ├── set <key> <value>    # Set config value
│   ├── get <key>            # Get config value
│   ├── list                 # List all config
│   └── profile              # Manage profiles
│       ├── create <name>
│       ├── use <name>
│       └── list
│
├── intent                   # Intent management
│   ├── submit <description> # Submit new intent
│   ├── list                 # List all intents
│   ├── get <id>             # Get intent details
│   ├── delete <id>          # Delete intent
│   ├── import <file>        # Import from file
│   ├── export <file>        # Export to file
│   └── templates            # Show example intents
│       ├── list
│       └── use <name>
│
├── policy                   # Policy management
│   ├── list                 # List all policies
│   ├── get <id>             # Get policy details
│   ├── apply <id>           # Apply policy
│   ├── rollback <id>        # Rollback policy
│   └── export <file>        # Export policies
│
├── network                  # Network enforcement
│   ├── status               # Show TC rules
│   ├── stats                # Show traffic stats
│   ├── clear                # Clear all rules
│   └── test <intent>        # Dry-run intent
│
├── device                   # IoT device management
│   ├── list                 # List all devices
│   ├── get <id>             # Get device details
│   └── status <id>          # Device status
│
├── monitor                  # Monitoring
│   ├── health               # System health check
│   ├── services             # Service status
│   ├── metrics <query>      # Query Prometheus
│   └── logs                 # View recent logs
│
└── version                  # Show CLI version
```

### 7.2 Global Flags

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--help` | `-h` | Show help | - |
| `--version` | `-v` | Show version | - |
| `--output` | `-o` | Output format (table/json/yaml) | table |
| `--quiet` | `-q` | Suppress non-essential output | false |
| `--verbose` | `-V` | Enable debug output | false |
| `--config` | `-c` | Config file path | ~/.imperium/config |
| `--profile` | `-p` | Use specific profile | default |
| `--api-url` | | Override API URL | from config |
| `--no-color` | | Disable colored output | false |

### 7.3 Command Examples

```bash
# Authentication
imperium login                              # Interactive login
imperium login -u admin -p admin            # Non-interactive
imperium login --api-key $API_KEY           # API key auth
imperium logout

# Intent Management
imperium intent submit "prioritize temperature sensors"
imperium intent submit "limit bandwidth to 50KB/s for cameras"
imperium intent submit "reduce latency to 20ms for sensor-01"
imperium intent list
imperium intent list --status active
imperium intent list --limit 10 --offset 0
imperium intent get intent-123
imperium intent delete intent-123
imperium intent import intents.yaml
imperium intent export --output intents.json

# Policy Management
imperium policy list
imperium policy list --type traffic_shaping
imperium policy get policy-456
imperium policy apply policy-456
imperium policy rollback policy-456

# Network
imperium network status
imperium network stats
imperium network stats --interface wlan0
imperium network clear --force
imperium network test "prioritize sensors"  # Dry-run

# Device Management
imperium device list
imperium device list --type sensor
imperium device get node-1
imperium device status node-1

# Monitoring
imperium monitor health
imperium monitor services
imperium monitor metrics "up"
imperium monitor metrics "rate(prometheus_http_requests_total[5m])"
imperium monitor logs --lines 50

# Configuration
imperium config set api_url http://192.168.1.8:5000
imperium config set output json
imperium config get api_url
imperium config list
imperium config profile create production
imperium config profile use production
```

---

## 8. User Stories

### 8.1 Authentication Stories

**US-001: First-time Login**
> As a new user, I want to authenticate with my credentials so that I can start using the CLI.

**Acceptance Criteria:**
- [ ] `imperium login` prompts for username and password
- [ ] Password is hidden during input
- [ ] Token is stored securely in ~/.imperium/credentials
- [ ] Success message displayed with expiry time
- [ ] Subsequent commands work without re-login

**US-002: Token Auto-refresh**
> As a user, I want my session to stay active so that I don't have to re-login frequently.

**Acceptance Criteria:**
- [ ] Token is automatically refreshed before expiry
- [ ] Refresh happens transparently during API calls
- [ ] User is notified only if refresh fails

### 8.2 Intent Management Stories

**US-003: Submit Intent**
> As a network admin, I want to submit an intent in natural language so that I can configure network policies quickly.

**Acceptance Criteria:**
- [ ] `imperium intent submit "description"` creates intent
- [ ] Output shows intent ID, parsed result, and policies generated
- [ ] Errors are displayed with helpful messages
- [ ] Command exits with code 0 on success, non-zero on failure

**US-004: List Intents**
> As a user, I want to see all my intents so that I can track what policies are active.

**Acceptance Criteria:**
- [ ] `imperium intent list` shows table with ID, description, status, date
- [ ] Supports pagination with --limit and --offset
- [ ] Supports filtering by status
- [ ] Output can be formatted as JSON/YAML

**US-005: Batch Import**
> As a DevOps engineer, I want to import intents from a file so that I can automate deployments.

**Acceptance Criteria:**
- [ ] `imperium intent import intents.yaml` processes file
- [ ] Supports both JSON and YAML formats
- [ ] Shows progress for multiple intents
- [ ] Reports success/failure for each intent

### 8.3 Network Stories

**US-006: View Network Status**
> As a network admin, I want to see current TC rules so that I can verify enforcement.

**Acceptance Criteria:**
- [ ] `imperium network status` shows active qdisc and classes
- [ ] Shows interface name and rule details
- [ ] Human-readable format with bandwidth units

**US-007: Dry-run Intent**
> As a user, I want to test an intent without applying it so that I can preview changes.

**Acceptance Criteria:**
- [ ] `imperium network test "intent"` shows what would happen
- [ ] No actual changes are made to the network
- [ ] Output shows TC commands that would be executed

### 8.4 Monitoring Stories

**US-008: Health Check**
> As an operator, I want to check system health so that I can ensure everything is running.

**Acceptance Criteria:**
- [ ] `imperium monitor health` shows API status
- [ ] Shows all features (auth, database, mqtt, etc.)
- [ ] Colored output (green=healthy, red=unhealthy)
- [ ] Exit code 0 if healthy, 1 if unhealthy

---

## 9. Technical Architecture

### 9.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.9+ | Matches existing codebase |
| CLI Framework | Click or Typer | Modern, type-hinted, auto-completion |
| HTTP Client | httpx or requests | Async support, connection pooling |
| Config Storage | YAML | Human-readable |
| Credential Storage | keyring or encrypted file | Platform-agnostic security |
| Output Formatting | rich | Tables, colors, progress bars |
| Testing | pytest + click.testing | CLI-specific testing utilities |

### 9.2 Project Structure

```
imperium-cli/
├── src/
│   └── imperium_cli/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── cli.py               # Main CLI group
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── auth.py          # login, logout
│       │   ├── intent.py        # intent commands
│       │   ├── policy.py        # policy commands
│       │   ├── network.py       # network commands
│       │   ├── device.py        # device commands
│       │   ├── monitor.py       # monitor commands
│       │   └── config.py        # config commands
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py        # API client
│       │   ├── auth.py          # Auth handling
│       │   └── models.py        # Data models
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py      # Config management
│       │   └── credentials.py   # Credential storage
│       ├── output/
│       │   ├── __init__.py
│       │   ├── formatters.py    # Table, JSON, YAML
│       │   └── colors.py        # Color themes
│       └── utils/
│           ├── __init__.py
│           ├── exceptions.py    # Custom exceptions
│           └── validators.py    # Input validation
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_intent.py
│   ├── test_policy.py
│   └── conftest.py
├── pyproject.toml               # Project metadata
├── README.md
└── LICENSE
```

### 9.3 API Client Design

```python
# Simplified API client interface
class ImperiumClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.token = token
    
    # Authentication
    def login(self, username: str, password: str) -> Token
    def refresh_token(self) -> Token
    
    # Intents
    def submit_intent(self, description: str) -> Intent
    def list_intents(self, limit: int, offset: int, status: str) -> List[Intent]
    def get_intent(self, intent_id: str) -> Intent
    def delete_intent(self, intent_id: str) -> bool
    
    # Policies
    def list_policies(self, type: str = None) -> List[Policy]
    def get_policy(self, policy_id: str) -> Policy
    def apply_policy(self, policy_id: str) -> bool
    
    # Network
    def get_network_status(self, interface: str) -> NetworkStatus
    def get_network_stats(self, interface: str) -> NetworkStats
    def clear_network_rules(self, interface: str) -> bool
    
    # Monitoring
    def health_check(self) -> HealthStatus
    def query_metrics(self, query: str) -> MetricResult
```

### 9.4 Configuration File Format

```yaml
# ~/.imperium/config.yaml
default_profile: development

profiles:
  development:
    api_url: http://localhost:5000
    output_format: table
    color: true
    timeout: 30
  
  production:
    api_url: http://192.168.1.8:5000
    output_format: json
    color: false
    timeout: 60

global:
  verbose: false
  auto_refresh_token: true
```

### 9.5 Credential Storage

```yaml
# ~/.imperium/credentials (encrypted)
profiles:
  development:
    token: "eyJhbGciOiJIUzI1NiIs..."
    expires_at: "2026-01-24T09:00:00Z"
    refresh_token: "..."
  
  production:
    api_key: "imp_live_xxxxx"
```

---

## 10. UI/UX Design

### 10.1 Output Examples

#### Table Output (Default)
```
$ imperium intent list

╭──────────────────────┬─────────────────────────────────────────┬──────────┬─────────────────────╮
│ ID                   │ Description                             │ Status   │ Created             │
├──────────────────────┼─────────────────────────────────────────┼──────────┼─────────────────────┤
│ intent-1-1769141074  │ prioritize temperature sensors and...   │ active   │ 2026-01-23 09:34:34 │
│ intent-2-1769141090  │ reduce latency to 20ms for sensor-01    │ active   │ 2026-01-23 09:34:50 │
│ intent-3-1769141115  │ set QoS level 2 for all critical...     │ active   │ 2026-01-23 09:35:15 │
╰──────────────────────┴─────────────────────────────────────────┴──────────┴─────────────────────╯

Showing 3 of 3 intents
```

#### JSON Output
```bash
$ imperium intent list -o json

{
  "intents": [
    {
      "id": "intent-1-1769141074",
      "description": "prioritize temperature sensors and limit bandwidth to 50KB/s for cameras",
      "status": "active",
      "created_at": "2026-01-23T09:34:34Z"
    }
  ],
  "total": 3,
  "limit": 50,
  "offset": 0
}
```

#### Intent Submission
```
$ imperium intent submit "prioritize temperature sensors"

✓ Intent submitted successfully

╭─────────────────────────────────────────────────────────╮
│ Intent Details                                          │
├─────────────────────────────────────────────────────────┤
│ ID:          intent-4-1769145000                        │
│ Description: prioritize temperature sensors             │
│ Type:        priority                                   │
│ Status:      active                                     │
├─────────────────────────────────────────────────────────┤
│ Parsed Parameters                                       │
├─────────────────────────────────────────────────────────┤
│ • priority: high                                        │
│ • devices: temp-*                                       │
├─────────────────────────────────────────────────────────┤
│ Generated Policies: 2                                   │
│ • policy-5: traffic_shaping (rate: 100mbit)            │
│ • policy-6: routing_priority (tos: 0x10)               │
╰─────────────────────────────────────────────────────────╯
```

#### Network Status
```
$ imperium network status

╭─────────────────────────────────────────────────────────╮
│ Network Enforcement Status                              │
├─────────────────────────────────────────────────────────┤
│ Interface: wlan0                                        │
│ Qdisc:     htb (handle 1:)                             │
│ Default:   class 1:30                                   │
├─────────────────────────────────────────────────────────┤
│ Traffic Classes                                         │
├──────────┬───────────┬───────────┬──────────┬──────────┤
│ Class    │ Rate      │ Ceil      │ Priority │ Packets  │
├──────────┼───────────┼───────────┼──────────┼──────────┤
│ 1:10     │ 100 Mbit  │ 200 Mbit  │ high     │ 0        │
│ 1:20     │ 50 Mbit   │ 100 Mbit  │ normal   │ 0        │
│ 1:30     │ 10 Mbit   │ 50 Mbit   │ low      │ 2,847    │
╰──────────┴───────────┴───────────┴──────────┴──────────╯
```

#### Health Check
```
$ imperium monitor health

╭─────────────────────────────────────────────────────────╮
│ System Health Check                                     │
├─────────────────────────────────────────────────────────┤
│ API Status:    ● healthy                                │
│ Service:       intent-manager                           │
├─────────────────────────────────────────────────────────┤
│ Features                                                │
├─────────────────────────────────────────────────────────┤
│ ✓ Authentication    enabled                             │
│ ✓ Database          connected                           │
│ ✓ Rate Limiting     enabled                             │
│ ✓ MQTT              connected                           │
│ ✓ Prometheus        scraping                            │
╰─────────────────────────────────────────────────────────╯

All systems operational ✓
```

#### Error Output
```
$ imperium intent submit ""

✗ Error: Intent description cannot be empty

Usage: imperium intent submit [OPTIONS] DESCRIPTION

  Submit a new intent in natural language.

Examples:
  imperium intent submit "prioritize temperature sensors"
  imperium intent submit "limit bandwidth to 100KB/s for cameras"
  imperium intent submit "reduce latency to 10ms for critical devices"

For more help: imperium intent submit --help
```

### 10.2 Interactive Mode

```
$ imperium intent submit

? Enter intent description: prioritize temperature sensors
? Confirm submission? [Y/n]: Y

✓ Intent submitted successfully
  ID: intent-4-1769145000
```

### 10.3 Progress Indicators

```
$ imperium intent import large_batch.yaml

Importing intents ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05

Results:
  ✓ 45 intents imported successfully
  ✗ 2 intents failed (see errors below)
  
Errors:
  Line 23: Invalid device pattern "***"
  Line 67: Bandwidth value out of range
```

---

## 11. Security Considerations

### 11.1 Credential Security

| Concern | Mitigation |
|---------|------------|
| Credentials in shell history | Use `--password-stdin` for scripts |
| Token exposure in environment | Store in encrypted file, not env vars |
| Insecure credential file | File permissions 600, encrypted content |
| Token in process list | Don't pass token as command argument |

### 11.2 Implementation

```bash
# Secure: Password via stdin
echo "password" | imperium login -u admin --password-stdin

# Secure: Environment variable for API key (CI/CD)
export IMPERIUM_API_KEY=xxx
imperium intent list

# Insecure (will warn): Password in command
imperium login -u admin -p password  # Warning displayed
```

### 11.3 Audit Logging

```yaml
# ~/.imperium/audit.log (optional, opt-in)
2026-01-23T09:34:34Z INFO  intent.submit description="prioritize..."
2026-01-23T09:35:00Z INFO  policy.apply policy_id=policy-5
2026-01-23T09:36:00Z WARN  auth.refresh token_expiring_soon=true
```

---

## 12. Success Metrics

### 12.1 Adoption Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily Active Users | 50+ | Telemetry (opt-in) |
| Commands per Session | 10+ | Telemetry |
| CLI vs API Usage | 80% CLI | API logs |

### 12.2 Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Command Latency (p50) | < 500ms | Telemetry |
| Command Latency (p99) | < 2s | Telemetry |
| Error Rate | < 1% | Error tracking |

### 12.3 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User Satisfaction | > 4.5/5 | Survey |
| Support Tickets | < 5/month | Helpdesk |
| Documentation Coverage | 100% | Manual review |

---

## 13. Implementation Phases

### 13.1 Phase 1: MVP (4 weeks)

**Week 1-2: Core Infrastructure**
- [ ] Project setup (pyproject.toml, structure)
- [ ] API client implementation
- [ ] Authentication (login, logout, token storage)
- [ ] Configuration management

**Week 3: Primary Commands**
- [ ] `imperium intent submit/list/get`
- [ ] `imperium policy list/get`
- [ ] `imperium monitor health`

**Week 4: Polish & Testing**
- [ ] Error handling
- [ ] Help text and examples
- [ ] Unit tests (80% coverage)
- [ ] Documentation

**MVP Deliverables:**
- Working CLI with core commands
- Secure authentication
- Table/JSON output formats
- Installation via pip

### 13.2 Phase 2: Enhanced Features (4 weeks)

**Week 5-6: Extended Commands**
- [ ] `imperium network status/stats/clear`
- [ ] `imperium device list/get/status`
- [ ] `imperium intent delete/import/export`
- [ ] `imperium policy apply/rollback`

**Week 7: UX Improvements**
- [ ] Auto-completion (Bash, Zsh, Fish)
- [ ] Interactive mode
- [ ] Progress indicators
- [ ] Color themes

**Week 8: Advanced Features**
- [ ] Profile management
- [ ] Dry-run mode
- [ ] Intent templates
- [ ] Batch operations

### 13.3 Phase 3: Enterprise Features (Future)

- [ ] SSO integration
- [ ] RBAC support
- [ ] Audit logging
- [ ] Plugin system
- [ ] Windows native support

---

## 14. Dependencies & Risks

### 14.1 Dependencies

| Dependency | Type | Impact if Delayed |
|------------|------|-------------------|
| Imperium API stability | Technical | High - CLI depends on API |
| Click/Typer library | External | Low - well-maintained |
| Python 3.9+ availability | Platform | Low - widely available |

### 14.2 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| API changes break CLI | Medium | High | Version compatibility layer |
| Token storage security issues | Low | High | Security audit, encryption |
| Cross-platform compatibility | Medium | Medium | CI testing on all platforms |
| User adoption resistance | Low | Medium | Good documentation, tutorials |

---

## 15. Appendix

### 15.1 Glossary

| Term | Definition |
|------|------------|
| Intent | Natural language description of desired network state |
| Policy | Concrete network configuration derived from intent |
| TC | Traffic Control - Linux kernel subsystem for QoS |
| HTB | Hierarchical Token Bucket - TC queueing discipline |
| QoS | Quality of Service |

### 15.2 References

- [Click Documentation](https://click.palletsprojects.com/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Library](https://rich.readthedocs.io/)
- [Imperium API Documentation](./API.md)

### 15.3 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-23 | Imperium Team | Initial draft |

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| Security Review | | | |

---

*End of Document*
