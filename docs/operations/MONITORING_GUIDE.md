# Grafana & Prometheus Monitoring Guide

Complete guide for monitoring IoT node traffic and intent impact using Grafana and Prometheus.

## Quick Access

- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3000 (admin/admin)
- **Prometheus API**: http://localhost:9090/api/v1

---

## Prometheus Queries for IoT Node Traffic

### 1. Check All IoT Node Targets

```bash
# Check which nodes Prometheus is scraping
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job | contains("iot")) | {job: .labels.job, instance: .labels.instance, health: .health}'
```

### 2. Node MQTT Message Rate

```promql
# Messages published per second by each node
rate(mqtt_messages_published_total[1m])

# Filter specific node
rate(mqtt_messages_published_total{node_id="node-1"}[1m])

# Total messages across all nodes
sum(rate(mqtt_messages_published_total[1m]))
```

### 3. Node Data Publishing Frequency

```promql
# Time between publishes (sampling rate)
mqtt_publish_interval_seconds

# Nodes publishing faster than 5 seconds
mqtt_publish_interval_seconds < 5
```

### 4. Node QoS Levels

```promql
# Current QoS level per node
mqtt_qos_level

# Nodes with QoS level 2 (highest priority)
mqtt_qos_level == 2
```

### 5. Node Priority Settings

```promql
# Check priority assignments
node_priority

# Count high priority nodes
count(node_priority{priority="high"})
```

### 6. Network Bandwidth Per Node

```promql
# Bytes sent per second
rate(node_bytes_sent_total[1m])

# Bandwidth in KB/s
rate(node_bytes_sent_total[1m]) / 1024

# Top 5 nodes by bandwidth
topk(5, rate(node_bytes_sent_total[1m]))
```

### 7. Node Latency Metrics

```promql
# Average latency per node
node_latency_milliseconds

# Nodes exceeding latency threshold
node_latency_milliseconds > 50

# 95th percentile latency
histogram_quantile(0.95, rate(node_latency_bucket[5m]))
```

---

## CLI Commands for Prometheus

### Query Prometheus from Terminal

```bash
# Generic query function
query_prometheus() {
    local query="$1"
    curl -s "http://localhost:9090/api/v1/query" \
        --data-urlencode "query=$query" | jq -r '.data.result'
}

# Example: Check all nodes
query_prometheus "up{job=~'.*iot.*'}"

# Check message rates
query_prometheus "rate(mqtt_messages_published_total[1m])"

# Get instant vector with labels
curl -s "http://localhost:9090/api/v1/query" \
    --data-urlencode "query=mqtt_qos_level" | \
    jq -r '.data.result[] | "\(.metric.node_id): QoS \(.value[1])"'
```

### Query Range (Time Series)

```bash
# Get last 5 minutes of data
curl -s "http://localhost:9090/api/v1/query_range" \
    --data-urlencode "query=rate(mqtt_messages_published_total[1m])" \
    --data-urlencode "start=$(date -u -d '5 minutes ago' +%s)" \
    --data-urlencode "end=$(date -u +%s)" \
    --data-urlencode "step=15s" | jq
```

### Check Node-Specific Metrics

```bash
# Get all metrics for node-1
curl -s http://localhost:8001/metrics | grep -E '^(mqtt|node)_'

# Get metrics from all IoT nodes
for port in {8001..8010}; do
    echo "=== Node on port $port ==="
    curl -s http://localhost:$port/metrics 2>/dev/null | grep '^mqtt_qos_level' || echo "Not available"
done
```

---

## Grafana Dashboard Setup

### Create Dashboard via API

```bash
# Login and get API key (manual step in UI: Configuration -> API Keys)
GRAFANA_API_KEY="your-api-key-here"

# Or use basic auth
GRAFANA_AUTH="admin:admin"

# Create dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_AUTH" \
    -d @- <<'EOF'
{
  "dashboard": {
    "title": "IoT Node Traffic & Intents",
    "panels": [
      {
        "id": 1,
        "title": "Node Message Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mqtt_messages_published_total[1m])",
            "legendFormat": "{{node_id}}"
          }
        ]
      }
    ]
  },
  "overwrite": true
}
EOF
```

### Add Data Source (Prometheus)

```bash
# Verify Prometheus data source
curl -s http://localhost:3000/api/datasources \
    -u admin:admin | jq '.[] | select(.type=="prometheus")'

# Add Prometheus if missing
curl -X POST http://localhost:3000/api/datasources \
    -H "Content-Type: application/json" \
    -u admin:admin \
    -d '{
      "name": "Prometheus",
      "type": "prometheus",
      "url": "http://imperium-prometheus:9090",
      "access": "proxy",
      "isDefault": true
    }'
```

---

## Monitoring Intent Impact on Nodes

### Step 1: Baseline Metrics (Before Intent)

```bash
# Save current state
echo "=== Baseline: $(date) ===" > baseline.txt

# Node message rates
curl -s "http://localhost:9090/api/v1/query" \
    --data-urlencode "query=rate(mqtt_messages_published_total[1m])" | \
    jq -r '.data.result[] | "\(.metric.node_id): \(.value[1]) msg/s"' >> baseline.txt

# QoS levels
curl -s "http://localhost:9090/api/v1/query" \
    --data-urlencode "query=mqtt_qos_level" | \
    jq -r '.data.result[] | "\(.metric.node_id): QoS \(.value[1])"' >> baseline.txt

cat baseline.txt
```

### Step 2: Submit Intent

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' | jq -r .token)

# Submit intent
INTENT_ID=$(curl -s -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description":"set QoS level 2 for node-1"}' | \
    jq -r '.intent.id')

echo "Intent ID: $INTENT_ID"
```

### Step 3: Monitor Changes

```bash
# Wait for enforcement (2-3 seconds)
sleep 3

# Check updated metrics
echo "=== After Intent: $(date) ===" > after.txt

curl -s "http://localhost:9090/api/v1/query" \
    --data-urlencode "query=mqtt_qos_level{node_id='node-1'}" | \
    jq -r '.data.result[] | "node-1 QoS: \(.value[1])"' >> after.txt

# Compare before/after
diff baseline.txt after.txt
```

### Step 4: Check Node Logs for Confirmation

```bash
# Verify node received MQTT control message
docker logs imperium-iot-node-1 --tail 20 | grep -i "control\|qos"
```

---

## Key Grafana Panels for Intent Monitoring

### Panel 1: Node Message Rate (Graph)

**PromQL Query:**

```promql
rate(mqtt_messages_published_total[1m])
```

**Legend Format:** `{{node_id}}`

**Use Case:** Track if bandwidth limits reduce message frequency

---

### Panel 2: QoS Level Changes (Stat/Table)

**PromQL Query:**

```promql
mqtt_qos_level
```

**Use Case:** Verify QoS intent enforcement

---

### Panel 3: Node Priority Heatmap

**PromQL Query:**

```promql
node_priority{priority="high"} * 3 or
node_priority{priority="normal"} * 2 or
node_priority{priority="low"} * 1
```

**Use Case:** Visualize priority distribution after "prioritize" intents

---

### Panel 4: Bandwidth Usage (Graph)

**PromQL Query:**

```promql
rate(node_bytes_sent_total[1m]) / 1024
```

**Unit:** KB/s

**Use Case:** Verify bandwidth limit enforcement

---

### Panel 5: Latency Over Time (Graph)

**PromQL Query:**

```promql
node_latency_milliseconds
```

**Threshold Alert:** `> 50ms`

**Use Case:** Track latency reduction intents

---

### Panel 6: Intent-to-Enforcement Latency

**PromQL Query:**

```promql
intent_enforcement_duration_seconds
```

**Use Case:** Measure system responsiveness

---

## Complete Monitoring Workflow

### 1. Real-Time Dashboard Watch

```bash
# Open Grafana dashboard
xdg-open http://localhost:3000/d/imperium-overview

# Or watch in terminal
watch -n 2 'curl -s "http://localhost:9090/api/v1/query" \
    --data-urlencode "query=mqtt_qos_level" | \
    jq -r ".data.result[] | \"\(.metric.node_id): QoS \(.value[1])\""'
```

### 2. Submit Intent and Monitor

```bash
# Terminal 1: Watch metrics
watch -n 1 'echo "=== $(date +%T) ==="; \
curl -s http://localhost:9090/api/v1/query \
    --data-urlencode "query=mqtt_qos_level{node_id=\"node-1\"}" | \
    jq -r ".data.result[0].value[1]"'

# Terminal 2: Submit intent
curl -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description":"set QoS level 2 for node-1"}'
```

### 3. Verify in Node Logs

```bash
# Watch node logs for control messages
docker logs -f imperium-iot-node-1 | grep --line-buffered "control\|qos\|config"
```

---

## Advanced Queries

### Track Intent Enforcement Latency

```promql
# Time from intent submission to policy enforcement
histogram_quantile(0.95,
  rate(intent_to_enforcement_seconds_bucket[5m])
)
```

### Nodes Affected by Recent Intents

```promql
# Count policy changes per node in last 5 minutes
increase(policy_updates_total[5m])
```

### Bandwidth Compliance

```promql
# Nodes exceeding bandwidth limits
(rate(node_bytes_sent_total[1m]) / 1024) >
  on(node_id) group_left node_bandwidth_limit_kbps
```

### QoS Upgrade Events

```promql
# Detect QoS level increases (intent enforcement)
delta(mqtt_qos_level[30s]) > 0
```

---

## Grafana Import Dashboard (JSON)

Save this as `iot-traffic-dashboard.json` and import via Grafana UI:

```json
{
  "dashboard": {
    "title": "IoT Node Traffic & Intent Impact",
    "tags": ["imperium", "iot"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Message Rate by Node",
        "type": "timeseries",
        "gridPos": { "x": 0, "y": 0, "w": 12, "h": 8 },
        "targets": [
          {
            "expr": "rate(mqtt_messages_published_total[1m])",
            "legendFormat": "{{node_id}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Current QoS Levels",
        "type": "stat",
        "gridPos": { "x": 12, "y": 0, "w": 12, "h": 8 },
        "targets": [
          {
            "expr": "mqtt_qos_level",
            "legendFormat": "{{node_id}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Bandwidth Usage (KB/s)",
        "type": "timeseries",
        "gridPos": { "x": 0, "y": 8, "w": 24, "h": 8 },
        "targets": [
          {
            "expr": "rate(node_bytes_sent_total[1m]) / 1024",
            "legendFormat": "{{node_id}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "KBs"
          }
        }
      }
    ]
  }
}
```

Import command:

```bash
curl -X POST http://localhost:3000/api/dashboards/import \
    -H "Content-Type: application/json" \
    -u admin:admin \
    -d @iot-traffic-dashboard.json
```

---

## Troubleshooting

### No Data in Grafana

```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check if IoT nodes expose metrics
curl -s http://localhost:8001/metrics | head -20

# Verify Grafana data source
curl -s http://localhost:3000/api/datasources -u admin:admin | jq '.[] | select(.type=="prometheus") | {name, url, basicAuth}'
```

### Metrics Not Updating After Intent

```bash
# Check API enforcement status
curl -s http://localhost:5000/health | jq

# Check MQTT broker
docker logs imperium-mqtt --tail 50 | grep -i "publish\|subscribe"

# Manually test MQTT control
docker exec imperium-mqtt mosquitto_pub \
    -t 'iot/node-1/control' \
    -m '{"qos": 2}'

# Wait 5s and check node metrics
sleep 5
curl -s http://localhost:8001/metrics | grep mqtt_qos_level
```

---

## Quick Reference Commands

```bash
# Check all node QoS levels
for i in {1..10}; do
    echo -n "node-$i: "
    curl -s http://localhost:800$i/metrics 2>/dev/null | \
        grep '^mqtt_qos_level' | awk '{print $2}' || echo "N/A"
done

# Submit test intent
curl -X POST http://localhost:5000/api/v1/intents \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"description":"prioritize node-1 and node-2"}'

# Watch Prometheus targets
watch -n 2 'curl -s http://localhost:9090/api/v1/targets | \
    jq -r ".data.activeTargets[] | select(.labels.job | contains(\"iot\")) | \
    \"\(.labels.instance): \(.health)\""'

# Open Grafana dashboard
xdg-open "http://localhost:3000/d/imperium-overview?refresh=5s"
```

---

## Integration with Demo Menu

The interactive demo menu (option 10 & 11) provides these monitoring features:

```bash
# Launch menu
demo

# Option 10: Prometheus Menu
#   - View targets, metrics, custom queries
#   - Live system metrics dashboard

# Option 11: Grafana Menu
#   - Access info, datasources, dashboards
#   - Direct browser links

# Option 14-16: Live Dashboards
#   - Auto-refreshing terminal-based monitoring
#   - Combined metrics view
```

---

## See Also

- [QUICKSTART.md](../setup/QUICKSTART.md) - Getting started guide
- [CODEBASE_INDEX.md](../development/CODEBASE_INDEX.md) - System architecture
- [SECURITY.md](../security/SECURITY.md) - MQTT TLS setup for production
