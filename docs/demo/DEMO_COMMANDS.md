# IMPERIUM IBN DEMO - COMMAND REFERENCE
## Complete Step-by-Step Guide with Explanations

---

## SETUP PHASE (Before Demo Starts)

### 1. Check Pi Network Connection
```bash
ping 192.168.1.8
```
**Purpose:** Verify Raspberry Pi is online and accessible
**Expected:** Continuous ping replies (Ctrl+C to stop)

### 2. SSH into Raspberry Pi
```bash
ssh imperium@192.168.1.8
```
**Purpose:** Remote access to Pi for running demo commands
**Expected:** Login prompt, then shell access

---

## PHASE 1: System Status Verification (Show Infrastructure)

### 3. Check Docker Containers
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -15
```
**Purpose:** Prove all services are running (MQTT, Prometheus, Grafana, 10 IoT nodes)
**Expected:** 13 containers with "Up" status
**What it shows:** The entire infrastructure is operational

### 4. Check Systemd Service
```bash
sudo systemctl status imperium --no-pager
```
**Purpose:** Show the main IBN controller is running as a system service
**Expected:** "active (running)" status
**What it shows:** Auto-starts on boot, managed by systemd

### 5. View System Resource Usage
```bash
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')%  |  Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
```
**Purpose:** Demonstrate low resource consumption
**Expected:** ~55% CPU, ~3GB/8GB RAM
**What it shows:** Efficient edge computing performance

---

## PHASE 2: API Health Check (Prove System Readiness)

### 6. Health Check Endpoint
```bash
curl -s http://localhost:5000/health | python3 -m json.tool
```
**Purpose:** Verify all features are enabled and working
**Expected:** JSON with status "healthy" and all features true
**What it shows:** Authentication, database, rate limiting, MQTT all operational

---

## PHASE 3: Authentication (Security Layer)

### 7. Login and Get JWT Token
```bash
curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python3 -m json.tool
```
**Purpose:** Authenticate as admin user to access protected endpoints
**Expected:** JSON response with JWT token (long string starting with "eyJ...")
**What it shows:** Security layer protecting network control APIs

### 8. Store Token for Subsequent Commands
```bash
TOKEN=$(curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
echo "Token acquired: ${TOKEN:0:60}..."
```
**Purpose:** Save token to reuse in later API calls (avoids re-authentication)
**Expected:** Confirmation message with truncated token
**What it shows:** Token-based authentication workflow

---

## PHASE 4: Intent Submission (THE CORE DEMO)

### 9. Submit Intent #1: Priority + Bandwidth Control
```bash
curl -s -X POST http://localhost:5000/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"prioritize temperature sensors and limit bandwidth to 50KB/s for cameras"}' | python3 -m json.tool
```
**Purpose:** Natural language → Network policy translation
**Expected:** JSON showing parsed intent with 2 actions (priority, bandwidth)
**What it shows:**
- Intent parser extracts device types (temp-*, camera-*)
- Policy engine generates bandwidth limits and priority queues
- No manual tc commands needed!

### 10. Submit Intent #2: Latency Optimization
```bash
curl -s -X POST http://localhost:5000/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"reduce latency to 20ms for sensor-01"}' | python3 -m json.tool
```
**Purpose:** Show latency-focused intent parsing
**Expected:** JSON with latency target extracted (20ms)
**What it shows:** Specific device targeting and latency enforcement

### 11. Submit Intent #3: QoS Configuration
```bash
curl -s -X POST http://localhost:5000/intents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"set QoS level 2 for all critical devices"}' | python3 -m json.tool
```
**Purpose:** Demonstrate MQTT QoS configuration via intent
**Expected:** JSON showing QoS level 2 assignment
**What it shows:** Device-level quality of service control

---

## PHASE 5: View Generated Policies (Show Translation)

### 12. List All Intents
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/intents | python3 -m json.tool
```
**Purpose:** Display all submitted intents and their parsed structure
**Expected:** Array of 4 intents (3 demo + 1 test) with parsed parameters
**What it shows:** How natural language is converted to structured data

### 13. Query Database Statistics
```bash
sqlite3 /home/imperium/Imperium/data/imperium.db "SELECT COUNT(*) as total_intents FROM intents; SELECT COUNT(*) as total_policies FROM policies;"
```
**Purpose:** Show persistent storage of intents and policies
**Expected:** Numbers matching submitted intents
**What it shows:** Intent history for audit and replay

---

## PHASE 6: Network Enforcement Proof (Real Linux TC)

### 14. Show Active Traffic Control Rules
```bash
IFACE=$(ip route | grep default | awk '{print $5}' | head -1)
echo "Active Interface: $IFACE"
sudo tc qdisc show dev $IFACE
```
**Purpose:** Prove REAL Linux kernel traffic shaping is applied
**Expected:** HTB qdisc with handle 1: root
**What it shows:** Not simulation - actual network enforcement

### 15. Show Traffic Classes (Bandwidth Limits)
```bash
sudo tc class show dev wlan0
```
**Purpose:** Display priority queues with rate limits
**Expected:** 3 classes (high/normal/low priority with different rates)
**What it shows:**
- class 1:10: 100Mbit (high priority for sensors)
- class 1:20: 50Mbit (normal priority)
- class 1:30: 10Mbit (low priority/default)

### 16. Show Traffic Statistics
```bash
sudo tc -s class show dev wlan0
```
**Purpose:** Prove packets are actually being shaped
**Expected:** Byte counts and packet counts (lended/borrowed stats)
**What it shows:** Real traffic is passing through the queues

---

## PHASE 7: Monitoring Stack (Prometheus + Grafana)

### 17. Query Prometheus Targets
```bash
curl -s "http://localhost:9090/api/v1/targets" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for t in d.get('data',{}).get('activeTargets',[]):
    print(f\"  {t['labels'].get('job')}: {t['health']}\")
"
```
**Purpose:** Show Prometheus is scraping metrics
**Expected:** "prometheus: up" status
**What it shows:** Monitoring infrastructure is collecting data

### 18. Count Available Metrics
```bash
curl -s "http://localhost:9090/api/v1/label/__name__/values" | python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f\"Available metrics: {len(d.get('data',[]))}\")"
```
**Purpose:** Demonstrate metrics collection capability
**Expected:** ~311 metrics available
**What it shows:** Extensive observability data

### 19. Access Grafana (In Browser)
**URL:** http://192.168.1.8:3000
**Credentials:** admin / admin

**What to do:**
1. Click hamburger menu (≡) → Explore
2. Select "Prometheus" data source
3. Query: `prometheus_http_requests_total`
4. Click "Run query" → See graph

**Purpose:** Show real-time visualization of system metrics
**What it shows:** Time-series graphs of network performance

---

## PHASE 8: IoT Node Status (Device Layer)

### 20. Check MQTT Broker
```bash
docker logs imperium-mqtt --tail 20
```
**Purpose:** Show MQTT broker handling device connections
**Expected:** Log entries showing client connections
**What it shows:** MQTT is the communication channel for IoT devices

### 21. Check IoT Node Activity
```bash
docker logs imperium-iot-node-1 --tail 10
```
**Purpose:** Show simulated IoT nodes are running
**Expected:** Connection logs and data publishing attempts
**What it shows:** Devices receiving policy updates via MQTT

---

## FINAL SUMMARY COMMAND

### 22. Complete System Status
```bash
echo "========================================" && \
echo "   IMPERIUM IBN SYSTEM STATUS" && \
echo "========================================" && \
echo "" && \
echo "Services Running:" && \
echo "  - API: $(systemctl is-active imperium)" && \
echo "  - Docker Containers: $(docker ps -q | wc -l)" && \
echo "" && \
echo "Network Enforcement:" && \
IFACE=$(ip route | grep default | awk '{print $5}' | head -1) && \
echo "  - Interface: $IFACE" && \
echo "  - TC Rules: $(sudo tc qdisc show dev $IFACE | wc -l) active" && \
echo "" && \
echo "Database:" && \
echo "  - Intents: $(sqlite3 /home/imperium/Imperium/data/imperium.db 'SELECT COUNT(*) FROM intents')" && \
echo "  - Policies: $(sqlite3 /home/imperium/Imperium/data/imperium.db 'SELECT COUNT(*) FROM policies')" && \
echo "" && \
echo "Access Points:" && \
echo "  - API: http://192.168.1.8:5000" && \
echo "  - Grafana: http://192.168.1.8:3000" && \
echo "  - Prometheus: http://192.168.1.8:9090"
```
**Purpose:** Single command to show entire system state
**Expected:** Complete status overview with all metrics
**What it shows:** Professional dashboard-style summary

---

## KEY TALKING POINTS FOR EACH PHASE

### When showing Docker containers (Cmd #3):
> "This system runs entirely on a Raspberry Pi 4. We have 10 simulated IoT nodes, an MQTT broker for device messaging, Prometheus for metrics, and Grafana for visualization - all orchestrated with Docker."

### When showing health check (Cmd #6):
> "The health endpoint proves all subsystems are operational. This is what a production monitoring system would query to ensure the service is ready."

### When showing authentication (Cmd #7):
> "Security is critical in network automation. Every API call requires a JWT token that expires after 24 hours. This prevents unauthorized policy changes."

### When submitting intents (Cmd #9-11):
> "This is the magic of Intent-Based Networking. I'm not writing tc commands or iptables rules - I'm expressing my goal in natural language, and the system handles the implementation."

### When showing TC rules (Cmd #14-16):
> "These aren't fake rules - these are real Linux kernel traffic control structures. If you ping a device right now, it will experience the bandwidth limits we defined. This is production-grade network shaping."

### When showing Grafana (Cmd #19):
> "Operators can monitor the entire network in real-time. If a policy isn't working, the feedback loop automatically adjusts it. This is closed-loop automation."

---

## DEMO FLOW SUMMARY (15 minutes total)

| Time | Commands | Purpose |
|------|----------|---------|
| 0-2 min | Cmd #1-5 | Prove system is running |
| 2-3 min | Cmd #6 | Health check |
| 3-5 min | Cmd #7-8 | Authentication |
| 5-10 min | Cmd #9-13 | **Core demo: Intent → Policy** |
| 10-12 min | Cmd #14-16 | **Proof: Real TC rules** |
| 12-14 min | Cmd #17-19 | Monitoring stack |
| 14-15 min | Cmd #22 | Final summary |

---

## BACKUP COMMANDS (If Something Breaks)

### Restart Services
```bash
sudo systemctl restart imperium
docker compose restart
```

### View Logs
```bash
journalctl -u imperium -n 50 --no-pager
docker logs imperium-mqtt --tail 50
```

### Reset TC Rules
```bash
sudo tc qdisc del dev wlan0 root 2>/dev/null
```

---

**Demo prepared on:** 2026-01-23
**System IP:** 192.168.1.8
**Status:** ✅ All commands verified working

