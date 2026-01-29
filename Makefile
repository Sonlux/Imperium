# Imperium Makefile - Quick Commands for Demo and Operations
# Usage: make <target>
# Example: make login, make submit, make status

.PHONY: help login health submit list-intents list-policies network docker status demo clean

# Configuration
API_URL ?= http://localhost:5000
USERNAME ?= admin
PASSWORD ?= admin

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Default target
help:
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║        IMPERIUM IBN - MAKEFILE COMMANDS (v2)             ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Authentication:$(NC)"
	@echo "  make login          - Login and get JWT token"
	@echo "  make health         - Check API health"
	@echo ""
	@echo "$(YELLOW)Intent Management:$(NC)"
	@echo "  make submit         - Submit example intent (interactive)"
	@echo "  make submit-priority - Submit: prioritize temperature sensors"
	@echo "  make submit-bandwidth - Submit: limit bandwidth to 50KB/s"
	@echo "  make submit-latency  - Submit: reduce latency to 20ms"
	@echo "  make list-intents   - List all intents"
	@echo "  make list-policies  - List all policies"
	@echo ""
	@echo "$(YELLOW)System Status:$(NC)"
	@echo "  make status         - Show full system status"
	@echo "  make docker         - Show Docker containers"
	@echo "  make network        - Show TC network rules"
	@echo "  make services       - Show systemd services"
	@echo ""
	@echo "$(GREEN)Monitoring:$(NC)"
	@echo "  make prometheus     - Show Prometheus targets & status"
	@echo "  make prometheus-query - Run custom PromQL query"
	@echo "  make prometheus-metrics - Show CPU/Memory/Series metrics"
	@echo "  make grafana        - Show Grafana access info & sources"
	@echo "  make grafana-add-prometheus - Add Prometheus data source"
	@echo ""
	@echo "$(GREEN)Live Dashboards:$(NC)"
	@echo "  make live           - Interactive menu with live dashboards"
	@echo "  make live-metrics   - Live auto-refreshing metrics"
	@echo ""
	@echo "$(YELLOW)Demo:$(NC)"
	@echo "  make demo           - Run interactive demo menu"
	@echo "  make demo-auto      - Run automated demo sequence"
	@echo ""
	@echo "$(YELLOW)Utilities:$(NC)"
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View API logs"
	@echo "  make clean          - Clear TC rules"
	@echo ""

# ============== Authentication ==============

# Store token in a file for reuse
.token:
	@curl -s -X POST $(API_URL)/api/v1/auth/login \
		-H "Content-Type: application/json" \
		-d '{"username":"$(USERNAME)","password":"$(PASSWORD)"}' | \
		python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" > .token
	@echo "$(GREEN)✓ Token saved to .token$(NC)"

login: .token
	@echo "$(GREEN)✓ Logged in as $(USERNAME)$(NC)"
	@echo "Token: $$(cat .token | head -c 50)..."

health:
	@echo "$(CYAN)Checking API health...$(NC)"
	@curl -s $(API_URL)/health | python3 -m json.tool

# ============== Intent Management ==============

submit: .token
	@echo "$(CYAN)Enter intent description:$(NC)"
	@read -p "> " INTENT && \
	curl -s -X POST $(API_URL)/api/v1/intents \
		-H "Authorization: Bearer $$(cat .token)" \
		-H "Content-Type: application/json" \
		-d "{\"description\":\"$$INTENT\"}" | python3 -m json.tool

submit-priority: .token
	@echo "$(CYAN)Submitting: prioritize temperature sensors$(NC)"
	@curl -s -X POST $(API_URL)/api/v1/intents \
		-H "Authorization: Bearer $$(cat .token)" \
		-H "Content-Type: application/json" \
		-d '{"description":"prioritize temperature sensors"}' | python3 -m json.tool

submit-bandwidth: .token
	@echo "$(CYAN)Submitting: limit bandwidth to 50KB/s for cameras$(NC)"
	@curl -s -X POST $(API_URL)/api/v1/intents \
		-H "Authorization: Bearer $$(cat .token)" \
		-H "Content-Type: application/json" \
		-d '{"description":"limit bandwidth to 50KB/s for cameras"}' | python3 -m json.tool

submit-latency: .token
	@echo "$(CYAN)Submitting: reduce latency to 20ms for sensor-01$(NC)"
	@curl -s -X POST $(API_URL)/api/v1/intents \
		-H "Authorization: Bearer $$(cat .token)" \
		-H "Content-Type: application/json" \
		-d '{"description":"reduce latency to 20ms for sensor-01"}' | python3 -m json.tool

submit-qos: .token
	@echo "$(CYAN)Submitting: set QoS level 2 for critical devices$(NC)"
	@curl -s -X POST $(API_URL)/api/v1/intents \
		-H "Authorization: Bearer $$(cat .token)" \
		-H "Content-Type: application/json" \
		-d '{"description":"set QoS level 2 for all critical devices"}' | python3 -m json.tool

list-intents: .token
	@echo "$(CYAN)Listing all intents...$(NC)"
	@curl -s -H "Authorization: Bearer $$(cat .token)" \
		$(API_URL)/api/v1/intents | python3 -m json.tool

list-policies: .token
	@echo "$(CYAN)Listing all policies...$(NC)"
	@curl -s -H "Authorization: Bearer $$(cat .token)" \
		$(API_URL)/api/v1/policies | python3 -m json.tool

# ============== System Status ==============

status:
	@echo "$(CYAN)╔══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║               IMPERIUM SYSTEM STATUS                     ║$(NC)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)API Service:$(NC)"
	@systemctl is-active imperium && echo "  $(GREEN)● Running$(NC)" || echo "  $(RED)○ Stopped$(NC)"
	@echo ""
	@echo "$(YELLOW)Docker Containers:$(NC)"
	@echo "  Running: $$(docker ps -q | wc -l)"
	@echo ""
	@echo "$(YELLOW)Resources:$(NC)"
	@echo "  Memory: $$(free -h | awk '/^Mem:/ {print $$3 "/" $$2}')"
	@echo "  Disk: $$(df -h / | awk 'NR==2 {print $$3 "/" $$2}')"
	@echo ""
	@echo "$(YELLOW)Database:$(NC)"
	@echo "  Intents: $$(sqlite3 data/imperium.db 'SELECT COUNT(*) FROM intents' 2>/dev/null || echo 'N/A')"
	@echo "  Policies: $$(sqlite3 data/imperium.db 'SELECT COUNT(*) FROM policies' 2>/dev/null || echo 'N/A')"

docker:
	@echo "$(CYAN)Docker Containers:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -15

network:
	@echo "$(CYAN)Network Interface:$(NC)"
	@IFACE=$$(ip route | grep default | awk '{print $$5}' | head -1) && \
	echo "  Active: $$IFACE" && \
	echo "" && \
	echo "$(YELLOW)TC Qdisc:$(NC)" && \
	sudo tc qdisc show dev $$IFACE && \
	echo "" && \
	echo "$(YELLOW)TC Classes:$(NC)" && \
	sudo tc class show dev $$IFACE && \
	echo "" && \
	echo "$(YELLOW)TC Statistics:$(NC)" && \
	sudo tc -s class show dev $$IFACE 2>/dev/null | head -25

services:
	@echo "$(CYAN)Systemd Services:$(NC)"
	@systemctl status imperium --no-pager -l | head -15

# ============== Demo ==============

demo:
	@python3 scripts/demo_menu.py

demo-auto:
	@echo "$(CYAN)Running automated demo sequence...$(NC)"
	@echo ""
	@$(MAKE) health
	@echo ""
	@$(MAKE) login
	@echo ""
	@$(MAKE) submit-priority
	@sleep 1
	@$(MAKE) submit-latency
	@sleep 1
	@$(MAKE) submit-qos
	@echo ""
	@$(MAKE) list-intents
	@echo ""
	@$(MAKE) network
	@echo ""
	@echo "$(GREEN)✓ Demo complete!$(NC)"

# ============== Service Management ==============

start:
	@echo "$(CYAN)Starting services...$(NC)"
	@docker compose up -d
	@sudo systemctl start imperium
	@echo "$(GREEN)✓ Services started$(NC)"

stop:
	@echo "$(CYAN)Stopping services...$(NC)"
	@sudo systemctl stop imperium
	@docker compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart:
	@echo "$(CYAN)Restarting services...$(NC)"
	@sudo systemctl restart imperium
	@docker compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

logs:
	@journalctl -u imperium -n 50 --no-pager

logs-follow:
	@journalctl -u imperium -f

# ============== Utilities ==============

clean:
	@echo "$(CYAN)Clearing TC rules...$(NC)"
	@IFACE=$$(ip route | grep default | awk '{print $$5}' | head -1) && \
	sudo tc qdisc del dev $$IFACE root 2>/dev/null || true
	@rm -f .token
	@echo "$(GREEN)✓ TC rules cleared, token removed$(NC)"

apply-tc:
	@echo "$(CYAN)Applying demo TC rules...$(NC)"
	@IFACE=$$(ip route | grep default | awk '{print $$5}' | head -1) && \
	sudo tc qdisc replace dev $$IFACE root handle 1: htb default 30 && \
	sudo tc class add dev $$IFACE parent 1: classid 1:10 htb rate 100mbit ceil 200mbit 2>/dev/null || true && \
	sudo tc class add dev $$IFACE parent 1: classid 1:20 htb rate 50mbit ceil 100mbit 2>/dev/null || true && \
	sudo tc class add dev $$IFACE parent 1: classid 1:30 htb rate 10mbit ceil 50mbit 2>/dev/null || true
	@echo "$(GREEN)✓ TC rules applied$(NC)"

prometheus:
	@echo "$(CYAN)Prometheus Status:$(NC)"
	@echo "  URL: http://localhost:9090"
	@echo ""
	@echo "$(YELLOW)Targets:$(NC)"
	@curl -s "http://localhost:9090/api/v1/targets" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f\"  {t['labels'].get('job')}: {t['health']}\") for t in d.get('data',{}).get('activeTargets',[])]" || echo "  Prometheus not reachable"
	@echo ""
	@echo "$(YELLOW)Metrics Count:$(NC)"
	@curl -s "http://localhost:9090/api/v1/label/__name__/values" 2>/dev/null | python3 -c "import sys,json; print(f\"  {len(json.load(sys.stdin).get('data',[]))} metrics available\")" || echo "  N/A"

prometheus-query:
	@echo "$(CYAN)Enter PromQL query:$(NC)"
	@read -p "> " QUERY && \
	curl -s "http://localhost:9090/api/v1/query?query=$$QUERY" | python3 -m json.tool

prometheus-metrics:
	@echo "$(CYAN)System Metrics from Prometheus:$(NC)"
	@echo ""
	@echo "$(YELLOW)CPU Usage:$(NC)"
	@curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=rate(process_cpu_seconds_total[1m])*100' 2>/dev/null | \
		python3 -c "import sys,json; r=json.load(sys.stdin).get('data',{}).get('result',[]); print(f\"  {float(r[0]['value'][1]):.2f}%\" if r else '  N/A')" || echo "  N/A"
	@echo ""
	@echo "$(YELLOW)Memory Usage:$(NC)"
	@curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=process_resident_memory_bytes/1024/1024' 2>/dev/null | \
		python3 -c "import sys,json; r=json.load(sys.stdin).get('data',{}).get('result',[]); print(f\"  {float(r[0]['value'][1]):.2f} MB\" if r else '  N/A')" || echo "  N/A"
	@echo ""
	@echo "$(YELLOW)Time Series:$(NC)"
	@curl -s 'http://localhost:9090/api/v1/query' --data-urlencode 'query=prometheus_tsdb_head_series' 2>/dev/null | \
		python3 -c "import sys,json; r=json.load(sys.stdin).get('data',{}).get('result',[]); print(f\"  {int(float(r[0]['value'][1]))}\" if r else '  N/A')" || echo "  N/A"

grafana:
	@echo "$(CYAN)Grafana Access:$(NC)"
	@echo "  URL: http://localhost:3000"
	@echo "  Username: admin"
	@echo "  Password: admin"
	@echo ""
	@echo "$(YELLOW)Health:$(NC)"
	@curl -s http://localhost:3000/api/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"  Database: {d.get('database','unknown')}\")" || echo "  Grafana not reachable"
	@echo ""
	@echo "$(YELLOW)Data Sources:$(NC)"
	@curl -s -u admin:admin http://localhost:3000/api/datasources 2>/dev/null | python3 -c "import sys,json; [print(f\"  - {ds.get('name')}: {ds.get('type')}\") for ds in json.load(sys.stdin)]" || echo "  N/A"

grafana-add-prometheus:
	@echo "$(CYAN)Adding Prometheus data source to Grafana...$(NC)"
	@curl -s -X POST http://localhost:3000/api/datasources \
		-u admin:admin \
		-H "Content-Type: application/json" \
		-d '{"name":"Prometheus","type":"prometheus","url":"http://localhost:9090","access":"proxy","isDefault":true}' | \
		python3 -c "import sys,json; d=json.load(sys.stdin); print('$(GREEN)✓ Added$(NC)' if 'id' in d else f\"Status: {d.get('message','unknown')}\")"

# Live monitoring (runs in loop)
live:
	@python3 scripts/demo_menu.py

live-metrics:
	@echo "$(CYAN)Starting live metrics (Ctrl+C to stop)...$(NC)"
	@while true; do \
		clear; \
		echo "$(CYAN)═══════════════ LIVE METRICS [$$(date +%H:%M:%S)] ═══════════════$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Prometheus Targets:$(NC)"; \
		curl -s "http://localhost:9090/api/v1/targets" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f\"  {t['labels'].get('job')}: {t['health']}\") for t in d.get('data',{}).get('activeTargets',[])]" || echo "  N/A"; \
		echo ""; \
		echo "$(YELLOW)Docker:$(NC) $$(docker ps -q | wc -l) containers"; \
		echo "$(YELLOW)Memory:$(NC) $$(free -h | awk '/^Mem:/ {print $$3 \"/\" $$2}')"; \
		echo "$(YELLOW)Intents:$(NC) $$(sqlite3 data/imperium.db 'SELECT COUNT(*) FROM intents' 2>/dev/null || echo 'N/A')"; \
		echo ""; \
		echo "$(DIM)Refreshing every 2s...$(NC)"; \
		sleep 2; \
	done

# ============== Quick Aliases ==============

# Short aliases for common commands
l: login
h: health
s: status
d: docker
n: network
i: list-intents
p: list-policies
prom: prometheus
graf: grafana
