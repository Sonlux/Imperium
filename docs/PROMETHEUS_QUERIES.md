# Prometheus & Grafana Queries Reference

**Generated:** 2026-02-03  
**Imperium IBN Framework**

## Quick Access

- **Prometheus:** http://192.168.1.100:9090
- **Grafana:** http://192.168.1.100:3000 (admin/admin)
- **Prometheus Graph:** http://192.168.1.100:9090/graph
- **Grafana Explore:** http://192.168.1.100:3000/explore

---

## Basic Status Queries

```promql
# Check if all services are up
up

# Count running targets
count(up == 1)

# Show only down targets
up == 0

# All IoT nodes status
up{job="iot-nodes"}

# Specific node status
up{job="iot-nodes",instance="imperium-iot-node-1:8001"}
```

---

## IoT Node Metrics

### Temperature Queries

```promql
# All node temperatures
node_temperature_celsius

# Specific node temperature
node_temperature_celsius{node_id="node-1"}

# Nodes with high temperature (>75°C)
node_temperature_celsius > 75

# Average temperature across all nodes
avg(node_temperature_celsius)

# Max temperature
max(node_temperature_celsius)

# Min temperature
min(node_temperature_celsius)

# Temperature by node (grouped)
sum by (node_id) (node_temperature_celsius)

# Temperature sorted (top 5 hottest)
topk(5, node_temperature_celsius)

# Temperature sorted (bottom 3 coolest)
bottomk(3, node_temperature_celsius)

# Temperature range
max(node_temperature_celsius) - min(node_temperature_celsius)
```

---

## Network & Bandwidth Queries

### Bandwidth Metrics

```promql
# Total bandwidth (bytes)
node_bandwidth_bytes_total

# Bandwidth rate (bytes/second) over 5 minutes
rate(node_bandwidth_bytes_total[5m])

# Total bandwidth across all nodes
sum(rate(node_bandwidth_bytes_total[5m]))

# Bandwidth by node
sum by (node_id) (rate(node_bandwidth_bytes_total[5m]))

# Bandwidth by node (KB/s)
rate(node_bandwidth_bytes_total[5m]) / 1024

# Bandwidth by node (MB/s)
rate(node_bandwidth_bytes_total[5m]) / 1024 / 1024

# Total network throughput (MB/s)
sum(rate(node_bandwidth_bytes_total[5m])) / 1024 / 1024

# Top 5 nodes by bandwidth usage
topk(5, rate(node_bandwidth_bytes_total[5m]))

# Nodes using > 100KB/s
rate(node_bandwidth_bytes_total[5m]) > 102400

# Bandwidth increase over 1 hour
increase(node_bandwidth_bytes_total[1h])
```

---

## Latency Queries

```promql
# Current latency (all nodes)
node_latency_ms

# Average latency
avg(node_latency_ms)

# Max latency
max(node_latency_ms)

# Min latency
min(node_latency_ms)

# Latency by node
sum by (node_id) (node_latency_ms)

# Nodes with high latency (>100ms)
node_latency_ms > 100

# Nodes with low latency (<20ms)
node_latency_ms < 20

# 95th percentile latency
quantile(0.95, node_latency_ms)

# 99th percentile latency
quantile(0.99, node_latency_ms)

# Latency change over 5 minutes
delta(node_latency_ms[5m])

# Average latency over 1 hour
avg_over_time(node_latency_ms[1h])
```

---

## Packet Loss & Quality Queries

```promql
# Packet loss rate
rate(node_packets_dropped_total[5m])

# Total packets sent
rate(node_packets_sent_total[5m])

# Packet loss percentage
(rate(node_packets_dropped_total[5m]) / rate(node_packets_sent_total[5m])) * 100

# Packet success rate
(1 - (rate(node_packets_dropped_total[5m]) / rate(node_packets_sent_total[5m]))) * 100

# QoS level
node_qos_level

# Messages sent per second
rate(node_messages_sent_total[1m])

# Total messages across all nodes
sum(rate(node_messages_sent_total[1m]))
```

---

## System Resource Queries

### Prometheus Internals

```promql
# Prometheus memory usage (bytes)
process_resident_memory_bytes{job="prometheus"}

# Prometheus memory usage (MB)
process_resident_memory_bytes{job="prometheus"} / 1024 / 1024

# Prometheus CPU usage
rate(process_cpu_seconds_total{job="prometheus"}[5m])

# Scrape duration (how long scrapes take)
scrape_duration_seconds

# Average scrape duration
avg(scrape_duration_seconds)

# Failed scrapes
up == 0

# Scrape samples ingested
scrape_samples_scraped

# Time series count
prometheus_tsdb_symbol_table_size_bytes
```

---

## Time-Based Queries

```promql
# Temperature change over 5 minutes
delta(node_temperature_celsius[5m])

# Temperature change over 1 hour
delta(node_temperature_celsius[1h])

# Bandwidth increase rate over 1 hour
increase(node_bandwidth_bytes_total[1h])

# Average temperature over 1 hour
avg_over_time(node_temperature_celsius[1h])

# Maximum temperature in last 24 hours
max_over_time(node_temperature_celsius[24h])

# Minimum latency in last 30 minutes
min_over_time(node_latency_ms[30m])

# Count samples over time
count_over_time(node_temperature_celsius[5m])
```

---

## Alerting Queries

### Critical Alerts

```promql
# Critical temperature alert (>80°C)
node_temperature_celsius > 80

# High temperature warning (>75°C)
node_temperature_celsius > 75

# High latency alert (>200ms)
node_latency_ms > 200

# Very high latency critical (>500ms)
node_latency_ms > 500

# Node offline for more than 1 minute
up{job="iot-nodes"} == 0

# High packet loss (>5%)
(rate(node_packets_dropped_total[5m]) / rate(node_packets_sent_total[5m])) * 100 > 5

# Bandwidth threshold exceeded (>1MB/s)
rate(node_bandwidth_bytes_total[5m]) > 1048576

# Low bandwidth (<10KB/s)
rate(node_bandwidth_bytes_total[5m]) < 10240

# Scrape taking too long (>5 seconds)
scrape_duration_seconds > 5

# Memory usage high (>1GB)
process_resident_memory_bytes > 1073741824
```

---

## Aggregation Queries

```promql
# Count active nodes
count(up{job="iot-nodes"} == 1)

# Count inactive nodes
count(up{job="iot-nodes"} == 0)

# Total nodes
count(up{job="iot-nodes"})

# Sum all bandwidth
sum(rate(node_bandwidth_bytes_total[5m]))

# Average temperature grouped by node
avg by (node_id) (node_temperature_celsius)

# Average latency grouped by node
avg by (node_id) (node_latency_ms)

# Top 5 nodes by bandwidth
topk(5, rate(node_bandwidth_bytes_total[5m]))

# Bottom 3 nodes by temperature
bottomk(3, node_temperature_celsius)

# Standard deviation of temperature
stddev(node_temperature_celsius)

# Variance in latency
stdvar(node_latency_ms)
```

---

## Multi-Metric Queries

```promql
# Temperature AND latency for same nodes
node_temperature_celsius and node_latency_ms

# High temp OR high latency nodes
node_temperature_celsius > 75 or node_latency_ms > 150

# Nodes with both high temp AND high latency
node_temperature_celsius > 75 and node_latency_ms > 150

# Bandwidth efficiency (bytes/s per degree)
rate(node_bandwidth_bytes_total[5m]) / node_temperature_celsius

# Nodes NOT experiencing high latency
node_latency_ms unless node_latency_ms > 100

# All metrics for a specific node
{node_id="node-1"}
```

---

## Rate Calculations

```promql
# Messages per second (1 minute rate)
rate(node_messages_sent_total[1m])

# Messages per second (5 minute rate)
rate(node_messages_sent_total[5m])

# Error rate
rate(node_errors_total[5m])

# Increase over 5 minutes
increase(node_bandwidth_bytes_total[5m])

# Increase over 1 hour
increase(node_bandwidth_bytes_total[1h])

# Per-second average over 5 minutes
avg_over_time(rate(node_bandwidth_bytes_total[1m])[5m:])

# Derivative (rate of change)
deriv(node_temperature_celsius[5m])
```

---

## Grafana Dashboard Queries

### For Different Panel Types

**Gauge Panel (Current Temperature)**
```promql
node_temperature_celsius{node_id="$node"}
```

**Graph Panel (Temperature Over Time)**
```promql
node_temperature_celsius
```

**Stat Panel (Total Active Nodes)**
```promql
count(up{job="iot-nodes"} == 1)
```

**Table Panel (All Node Metrics)**
```promql
node_temperature_celsius
node_latency_ms
rate(node_bandwidth_bytes_total[5m])
node_qos_level
```

**Heatmap (Latency Distribution)**
```promql
histogram_quantile(0.5, rate(node_latency_ms[5m]))
histogram_quantile(0.95, rate(node_latency_ms[5m]))
histogram_quantile(0.99, rate(node_latency_ms[5m]))
```

**Bar Gauge (Bandwidth by Node)**
```promql
sum by (node_id) (rate(node_bandwidth_bytes_total[5m]))
```

**Pie Chart (Node Status)**
```promql
count(up{job="iot-nodes"} == 1)
count(up{job="iot-nodes"} == 0)
```

---

## Custom Imperium Metrics

```promql
# Intent satisfaction ratio
ibs_intent_satisfaction_ratio

# Policy enforcement latency (seconds)
ibs_policy_enforcement_latency_seconds

# Policy enforcement latency (milliseconds)
ibs_policy_enforcement_latency_seconds * 1000

# Active policies count
ibs_active_policies_total

# Intent processing time
rate(ibs_intent_processing_seconds[5m])

# Average intent processing time
avg(ibs_intent_processing_seconds)

# Successful policy enforcements
ibs_policy_enforcement_success_total

# Failed policy enforcements
ibs_policy_enforcement_failure_total

# Policy enforcement success rate
ibs_policy_enforcement_success_total / (ibs_policy_enforcement_success_total + ibs_policy_enforcement_failure_total)
```

---

## Troubleshooting Queries

```promql
# Missing metrics (no data for node-1 temperature)
absent(node_temperature_celsius{node_id="node-1"})

# Stale metrics (not updated in 1 minute)
time() - timestamp(node_temperature_celsius) > 60

# Very stale metrics (not updated in 5 minutes)
time() - timestamp(node_temperature_celsius) > 300

# Scrape failures
up == 0

# High scrape duration (>5 seconds)
scrape_duration_seconds > 5

# Scrape errors
scrape_samples_post_metric_relabeling == 0

# Target down for more than 5 minutes
up{job="iot-nodes"} == 0 and time() - timestamp(up{job="iot-nodes"}) > 300

# Prometheus storage full
prometheus_tsdb_storage_blocks_bytes / prometheus_tsdb_retention_limit_bytes > 0.9
```

---

## Advanced Queries

### Correlation Analysis

```promql
# Temperature vs Latency correlation
node_temperature_celsius * node_latency_ms

# Bandwidth utilization percentage (assuming 1Mbps capacity)
(rate(node_bandwidth_bytes_total[5m]) / 125000) * 100

# Network efficiency score
(rate(node_messages_sent_total[5m]) / rate(node_packets_sent_total[5m])) * 100

# QoS compliance (latency within target)
(node_latency_ms < 100) * 1
```

### Prediction Queries

```promql
# Predict temperature in 10 minutes (linear)
predict_linear(node_temperature_celsius[30m], 600)

# Predict bandwidth usage in 1 hour
predict_linear(node_bandwidth_bytes_total[30m], 3600)
```

### Window Functions

```promql
# Rolling average (5 minute window)
avg_over_time(node_temperature_celsius[5m])

# Moving maximum
max_over_time(node_latency_ms[5m])

# Rate of change
deriv(node_temperature_celsius[5m])

# Absolute rate of change
abs(deriv(node_temperature_celsius[5m]))
```

---

## Command Line Queries

### Using curl

```bash
# Query current temperature
curl -G http://192.168.1.100:9090/api/v1/query \
  --data-urlencode 'query=node_temperature_celsius' | jq

# Query with time range
curl -G http://192.168.1.100:9090/api/v1/query_range \
  --data-urlencode 'query=node_temperature_celsius' \
  --data-urlencode 'start=2026-02-03T00:00:00Z' \
  --data-urlencode 'end=2026-02-03T23:59:59Z' \
  --data-urlencode 'step=15s' | jq

# Check node status
curl -G http://192.168.1.100:9090/api/v1/query \
  --data-urlencode 'query=up{job="iot-nodes"}' | jq '.data.result[] | {instance: .metric.instance, status: .value[1]}'

# Get all available metrics
curl http://192.168.1.100:9090/api/v1/label/__name__/values | jq
```

---

## Query Best Practices

### Performance Tips

1. **Use appropriate time ranges**
   - Short queries: `[1m]`, `[5m]`
   - Medium queries: `[15m]`, `[1h]`
   - Long queries: `[24h]`, `[7d]`

2. **Limit result sets**
   - Use `topk()` or `bottomk()` instead of returning all series
   - Filter with label selectors: `{node_id="node-1"}`

3. **Use rate() for counters**
   - Always use `rate()` or `increase()` for counter metrics
   - Example: `rate(node_bandwidth_bytes_total[5m])`

4. **Avoid high-cardinality queries**
   - Don't group by unique values like timestamps
   - Limit `by` clauses to necessary labels

### Common Patterns

```promql
# Counter metric pattern
rate(metric_name_total[5m])

# Gauge metric pattern
metric_name

# Percentage calculation
(part / total) * 100

# Threshold check
metric_name > threshold

# Aggregation pattern
sum by (label_name) (metric_name)
```

---

## Quick Reference Table

| Metric | Query | Unit |
|--------|-------|------|
| Temperature | `node_temperature_celsius` | °C |
| Latency | `node_latency_ms` | ms |
| Bandwidth | `rate(node_bandwidth_bytes_total[5m])` | bytes/s |
| QoS Level | `node_qos_level` | 0-2 |
| Packet Loss | `rate(node_packets_dropped_total[5m])` | packets/s |
| Messages | `rate(node_messages_sent_total[1m])` | msg/s |
| Node Status | `up{job="iot-nodes"}` | 0 or 1 |

---

## Resources

- **PromQL Documentation:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Query Editor:** http://192.168.1.100:3000/explore
- **Prometheus Web UI:** http://192.168.1.100:9090/graph
- **Query Examples:** https://prometheus.io/docs/prometheus/latest/querying/examples/

---

**Last Updated:** 2026-02-03  
**Imperium Version:** 1.0.0  
**Prometheus:** Latest  
**Grafana:** Latest
