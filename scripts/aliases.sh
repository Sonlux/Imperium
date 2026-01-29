#!/bin/bash
# Imperium Shell Aliases (Enhanced v2)
# Source this file: source scripts/aliases.sh
# Or add to ~/.bashrc: source /home/imperium/Imperium/scripts/aliases.sh

# Navigate to project
alias imp='cd /home/imperium/Imperium'

# Interactive Demo Menu (RECOMMENDED)
alias demo='python3 /home/imperium/Imperium/scripts/demo_menu.py'
alias live='python3 /home/imperium/Imperium/scripts/demo_menu.py'

# Quick commands using make
alias imp-login='cd /home/imperium/Imperium && make login'
alias imp-health='cd /home/imperium/Imperium && make health'
alias imp-status='cd /home/imperium/Imperium && make status'
alias imp-docker='cd /home/imperium/Imperium && make docker'
alias imp-network='cd /home/imperium/Imperium && make network'
alias imp-intents='cd /home/imperium/Imperium && make list-intents'
alias imp-policies='cd /home/imperium/Imperium && make list-policies'

# Submit intents
alias imp-submit='cd /home/imperium/Imperium && make submit'
alias imp-priority='cd /home/imperium/Imperium && make submit-priority'
alias imp-bandwidth='cd /home/imperium/Imperium && make submit-bandwidth'
alias imp-latency='cd /home/imperium/Imperium && make submit-latency'
alias imp-qos='cd /home/imperium/Imperium && make submit-qos'

# Monitoring - NEW!
alias imp-prom='cd /home/imperium/Imperium && make prometheus'
alias imp-grafana='cd /home/imperium/Imperium && make grafana'
alias imp-metrics='cd /home/imperium/Imperium && make prometheus-metrics'
alias imp-live='cd /home/imperium/Imperium && make live-metrics'

# Service management
alias imp-start='cd /home/imperium/Imperium && make start'
alias imp-stop='cd /home/imperium/Imperium && make stop'
alias imp-restart='cd /home/imperium/Imperium && make restart'
alias imp-logs='cd /home/imperium/Imperium && make logs'

# Auto demo
alias imp-demo-auto='cd /home/imperium/Imperium && make demo-auto'

# Short aliases (even quicker!)
alias ilogin='imp-login'
alias ihealth='imp-health'
alias istatus='imp-status'
alias isubmit='imp-submit'
alias iprom='imp-prom'
alias igraf='imp-grafana'
alias ilive='imp-live'

echo "Imperium aliases loaded! Commands:"
echo "  demo          - Interactive menu with live dashboards"
echo "  imp-prom      - Prometheus status"
echo "  imp-grafana   - Grafana info"
echo "  imp-metrics   - Live metrics from Prometheus"
echo "  imp-status    - System overview"
