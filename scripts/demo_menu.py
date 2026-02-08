#!/usr/bin/env python3
"""
Imperium Interactive Demo Menu - Enhanced Version v3
Features:
- Prometheus metrics integration
- Grafana dashboard links
- Live dynamic monitoring with auto-refresh
- Real-time system status
- IoT node detailed views
- MQTT messaging

Run with: python3 scripts/demo_menu.py
      or: demo (if aliases are loaded)
"""
import requests
import json
import subprocess
import os
import sys
import time
import webbrowser
from datetime import datetime

# Configuration
API_URL = os.getenv("IMPERIUM_API_URL", "http://localhost:5000")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOKEN = None
REFRESH_INTERVAL = 2  # seconds for live updates

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    WHITE = '\033[97m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_json(data):
    print(f"{Colors.YELLOW}{json.dumps(data, indent=2)}{Colors.END}")

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def open_url(url):
    """Open URL in browser or show the link"""
    print_info(f"URL: {url}")
    try:
        # Try to open in browser
        result = subprocess.run(
            f"xdg-open '{url}' 2>/dev/null || open '{url}' 2>/dev/null",
            shell=True, capture_output=True
        )
        if result.returncode == 0:
            print_success("Opened in browser")
        else:
            print_info("Copy the URL above to open in your browser")
    except:
        print_info("Copy the URL above to open in your browser")

# ============== API Functions ==============

def login(username="admin", password="admin"):
    """Login and store token"""
    global TOKEN
    try:
        response = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            TOKEN = data.get("token")
            print_success(f"Logged in as {username}")
            print_info(f"Token: {TOKEN[:50]}...")
            return True
        else:
            print_error(f"Login failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False

def check_health():
    """Check API health"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        data = response.json()
        print_success("API is healthy")
        print_json(data)
        return data
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return None

def submit_intent(description):
    """Submit a new intent"""
    global TOKEN
    if not TOKEN:
        print_info("Auto-logging in...")
        login()
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/intents",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"description": description},
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            print_success("Intent submitted successfully!")
            intent = data.get("intent", data)
            print(f"\n{Colors.CYAN}Intent ID:{Colors.END} {intent.get('id')}")
            print(f"{Colors.CYAN}Type:{Colors.END} {intent.get('type')}")
            print(f"{Colors.CYAN}Status:{Colors.END} {intent.get('status')}")
            
            # Show parsed data
            parsed = intent.get('parsed', {})
            if parsed:
                print(f"\n{Colors.YELLOW}Parsed Parameters:{Colors.END}")
                print_json(parsed.get('parameters', {}))
            
            # Show policies
            policies = intent.get('policies', [])
            if policies:
                print(f"\n{Colors.GREEN}Generated Policies: {len(policies)}{Colors.END}")
                for p in policies:
                    print(f"  • {p.get('policy_type')}: {p.get('target', 'N/A')}")
            return intent
        else:
            print_error(f"Failed: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def list_intents():
    """List all intents"""
    global TOKEN
    if not TOKEN:
        print_info("Auto-logging in...")
        login()
    
    try:
        response = requests.get(
            f"{API_URL}/api/v1/intents",
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            intents = data.get("intents", [])
            print_success(f"Found {len(intents)} intents")
            print()
            
            # Print table header
            print(f"{Colors.BOLD}{'ID':<25} {'Type':<12} {'Status':<10} {'Description':<40}{Colors.END}")
            print("-" * 90)
            
            for intent in intents:
                desc = intent.get('original_intent', intent.get('description', ''))[:38]
                int_type = intent.get('parsed_intent', {}).get('type', 'N/A')
                print(f"{intent.get('id', 'N/A'):<25} "
                      f"{int_type:<12} "
                      f"{intent.get('status', 'N/A'):<10} "
                      f"{desc:<40}")
            return intents
        else:
            print_error(f"Failed: {response.text}")
            return []
    except Exception as e:
        print_error(f"Error: {e}")
        return []

def list_policies():
    """List all policies"""
    global TOKEN
    if not TOKEN:
        print_info("Auto-logging in...")
        login()
    
    try:
        response = requests.get(
            f"{API_URL}/api/v1/policies",
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            policies = data.get("policies", [])
            print_success(f"Found {len(policies)} policies")
            print_json(policies[:5])  # Show first 5
            return policies
        else:
            print_error(f"Failed: {response.text}")
            return []
    except Exception as e:
        print_error(f"Error: {e}")
        return []

# ============== Prometheus Functions ==============

def query_prometheus(query):
    """Execute a Prometheus query"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("data", {}).get("result", [])
        return []
    except:
        return []

def get_prometheus_targets():
    """Get Prometheus scrape targets status"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {}).get("activeTargets", [])
        return []
    except:
        return []

def get_prometheus_metrics_count():
    """Get count of available metrics"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/label/__name__/values", timeout=10)
        if response.status_code == 200:
            return len(response.json().get("data", []))
        return 0
    except:
        return 0

def prometheus_menu():
    """Prometheus monitoring menu"""
    while True:
        clear_screen()
        print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║              PROMETHEUS MONITORING                        ║
╠══════════════════════════════════════════════════════════╣{Colors.END}
{Colors.CYAN}  Queries:{Colors.END}
    1. Scrape Targets Status       2. Available Metrics Count
    3. HTTP Request Rate           4. CPU Usage
    5. Memory Usage                6. Active Time Series
    7. Custom PromQL Query
    
{Colors.GREEN}  Live Monitoring:{Colors.END}
    8. Live System Metrics (auto-refresh)
    9. Live Target Health (auto-refresh)
    
{Colors.YELLOW}   b. Back to Main Menu{Colors.END}
{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════╝{Colors.END}

{Colors.DIM}Prometheus URL: {PROMETHEUS_URL}{Colors.END}
""")
        
        choice = input(f"{Colors.CYAN}Select option:{Colors.END} ").strip().lower()
        
        if choice == 'b':
            break
        elif choice == '1':
            print_header("Prometheus Targets")
            targets = get_prometheus_targets()
            for t in targets:
                health = t.get('health', 'unknown')
                color = Colors.GREEN if health == 'up' else Colors.RED
                print(f"  {color}● {t.get('labels', {}).get('job', 'unknown')}: {health}{Colors.END}")
                print(f"    URL: {t.get('scrapeUrl', 'N/A')}")
                print(f"    Last Scrape: {t.get('lastScrapeDuration', 0)*1000:.2f}ms")
            input("\nPress Enter to continue...")
        elif choice == '2':
            print_header("Metrics Count")
            count = get_prometheus_metrics_count()
            print(f"  Total available metrics: {Colors.GREEN}{count}{Colors.END}")
            input("\nPress Enter to continue...")
        elif choice == '3':
            print_header("HTTP Request Rate (last 5m)")
            results = query_prometheus("rate(prometheus_http_requests_total[5m])")
            for r in results[:10]:
                handler = r.get('metric', {}).get('handler', 'unknown')
                value = float(r.get('value', [0, 0])[1])
                print(f"  {handler}: {value:.4f} req/s")
            input("\nPress Enter to continue...")
        elif choice == '4':
            print_header("CPU Usage")
            results = query_prometheus("rate(process_cpu_seconds_total[1m]) * 100")
            for r in results:
                value = float(r.get('value', [0, 0])[1])
                print(f"  CPU: {Colors.YELLOW}{value:.2f}%{Colors.END}")
            if not results:
                print_warning("No CPU data available")
            input("\nPress Enter to continue...")
        elif choice == '5':
            print_header("Memory Usage")
            results = query_prometheus("process_resident_memory_bytes / 1024 / 1024")
            for r in results:
                value = float(r.get('value', [0, 0])[1])
                print(f"  Memory: {Colors.YELLOW}{value:.2f} MB{Colors.END}")
            if not results:
                print_warning("No memory data available")
            input("\nPress Enter to continue...")
        elif choice == '6':
            print_header("Active Time Series")
            results = query_prometheus("prometheus_tsdb_head_series")
            for r in results:
                value = int(float(r.get('value', [0, 0])[1]))
                print(f"  Active series: {Colors.GREEN}{value}{Colors.END}")
            input("\nPress Enter to continue...")
        elif choice == '7':
            print_header("Custom PromQL Query")
            print(f"  {Colors.DIM}Examples: up, rate(prometheus_http_requests_total[5m]){Colors.END}")
            query = input(f"\n{Colors.CYAN}Enter PromQL query:{Colors.END} ").strip()
            if query:
                results = query_prometheus(query)
                if results:
                    for r in results[:20]:
                        metric = r.get('metric', {})
                        value = r.get('value', [0, 'N/A'])[1]
                        print(f"  {metric}: {value}")
                else:
                    print_warning("No results or invalid query")
            input("\nPress Enter to continue...")
        elif choice == '8':
            live_system_metrics()
        elif choice == '9':
            live_target_health()

def grafana_menu():
    """Grafana dashboard menu"""
    while True:
        clear_screen()
        print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║               GRAFANA DASHBOARDS                          ║
╠══════════════════════════════════════════════════════════╣{Colors.END}
{Colors.CYAN}  Quick Access:{Colors.END}
    1. Show Grafana Access Info    2. Check Grafana Health
    3. List Data Sources           4. Show Dashboard URLs
    
{Colors.CYAN}  Actions:{Colors.END}
    5. Show Example Queries        6. Add Prometheus Data Source
    7. Open Grafana in Browser     8. Open Prometheus in Browser
    
{Colors.YELLOW}   b. Back to Main Menu{Colors.END}
{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════╝{Colors.END}

{Colors.DIM}Grafana URL: {GRAFANA_URL}{Colors.END}
""")
        
        choice = input(f"{Colors.CYAN}Select option:{Colors.END} ").strip().lower()
        
        if choice == 'b':
            break
        elif choice == '1':
            print_header("Grafana Access")
            print(f"""
  {Colors.CYAN}URL:{Colors.END}      {GRAFANA_URL}
  {Colors.CYAN}Username:{Colors.END} admin
  {Colors.CYAN}Password:{Colors.END} admin
  
  {Colors.YELLOW}Quick Links:{Colors.END}
  • Home:       {GRAFANA_URL}/
  • Explore:    {GRAFANA_URL}/explore
  • Dashboards: {GRAFANA_URL}/dashboards
  
  {Colors.GREEN}To access from another computer:{Colors.END}
  Replace 'localhost' with your Pi's IP address
""")
            input("\nPress Enter to continue...")
        elif choice == '2':
            print_header("Grafana Health")
            try:
                response = requests.get(f"{GRAFANA_URL}/api/health", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print_success("Grafana is healthy")
                    print(f"  {Colors.CYAN}Database:{Colors.END} {data.get('database', 'unknown')}")
                    print(f"  {Colors.CYAN}Version:{Colors.END} {data.get('version', 'unknown')}")
                else:
                    print_error(f"Status: {response.status_code}")
            except Exception as e:
                print_error(f"Cannot reach Grafana: {e}")
            input("\nPress Enter to continue...")
        elif choice == '3':
            print_header("Data Sources")
            try:
                response = requests.get(
                    f"{GRAFANA_URL}/api/datasources",
                    auth=("admin", "admin"),
                    timeout=10
                )
                if response.status_code == 200:
                    sources = response.json()
                    if sources:
                        print(f"  Found {len(sources)} data source(s):\n")
                        for ds in sources:
                            status = f"{Colors.GREEN}●{Colors.END}" if ds.get('isDefault') else f"{Colors.CYAN}○{Colors.END}"
                            print(f"  {status} {ds.get('name')}")
                            print(f"      Type: {ds.get('type')}")
                            print(f"      URL: {ds.get('url')}")
                            print(f"      Default: {ds.get('isDefault', False)}")
                            print()
                    else:
                        print_warning("No data sources configured")
                        print_info("Use option 6 to add Prometheus data source")
            except Exception as e:
                print_error(f"Error: {e}")
            input("\nPress Enter to continue...")
        elif choice == '4':
            print_header("Dashboard URLs")
            print(f"""
  {Colors.CYAN}Pre-configured Dashboards:{Colors.END}
  • Imperium Overview: {GRAFANA_URL}/d/imperium-overview
  • Imperium Devices:  {GRAFANA_URL}/d/imperium-devices
  
  {Colors.CYAN}Create New:{Colors.END}
  • New Dashboard: {GRAFANA_URL}/dashboard/new
  • Import:        {GRAFANA_URL}/dashboard/import
  
  {Colors.CYAN}Explore (Ad-hoc Queries):{Colors.END}
  • {GRAFANA_URL}/explore
  
  {Colors.YELLOW}Tip:{Colors.END} In Explore, select 'Prometheus' as data source
       and enter any PromQL query to visualize data
""")
            input("\nPress Enter to continue...")
        elif choice == '5':
            show_example_queries()
            input("\nPress Enter to continue...")
        elif choice == '6':
            add_grafana_datasource()
            input("\nPress Enter to continue...")
        elif choice == '7':
            print_header("Opening Grafana")
            open_url(GRAFANA_URL)
            input("\nPress Enter to continue...")
        elif choice == '8':
            print_header("Opening Prometheus")
            open_url(PROMETHEUS_URL)
            input("\nPress Enter to continue...")

def show_example_queries():
    """Show example Prometheus queries for Grafana"""
    print_header("Example Prometheus Queries for Grafana")
    queries = [
        ("System Health", "up"),
        ("HTTP Request Rate", "rate(prometheus_http_requests_total[5m])"),
        ("CPU Usage %", "rate(process_cpu_seconds_total[1m]) * 100"),
        ("Memory (MB)", "process_resident_memory_bytes / 1024 / 1024"),
        ("Active Time Series", "prometheus_tsdb_head_series"),
        ("Scrape Duration", "scrape_duration_seconds"),
        ("Failed Scrapes", "up == 0"),
        ("Request Latency p95", "histogram_quantile(0.95, rate(prometheus_http_request_duration_seconds_bucket[5m]))"),
        ("Data Ingestion Rate", "rate(prometheus_tsdb_head_samples_appended_total[1m])"),
        ("Storage Size", "prometheus_tsdb_head_chunks_storage_size_bytes / 1024 / 1024"),
    ]
    
    for name, query in queries:
        print(f"  {Colors.CYAN}{name}:{Colors.END}")
        print(f"    {Colors.YELLOW}{query}{Colors.END}")
        print()

def add_grafana_datasource():
    """Add Prometheus as a data source in Grafana"""
    print_header("Add Prometheus Data Source")
    
    datasource = {
        "name": "Prometheus",
        "type": "prometheus",
        "url": "http://localhost:9090",
        "access": "proxy",
        "isDefault": True
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            json=datasource,
            auth=("admin", "admin"),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in [200, 201]:
            print_success("Prometheus data source added successfully!")
        elif response.status_code == 409:
            print_warning("Data source already exists")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")

# ============== Live Monitoring Functions ==============

def live_system_metrics():
    """Live updating system metrics dashboard"""
    print_info("Starting live monitoring... Press Ctrl+C to stop")
    time.sleep(1)
    
    try:
        while True:
            clear_screen()
            timestamp = get_timestamp()
            
            print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║          LIVE SYSTEM METRICS  [{timestamp}]              ║
╚══════════════════════════════════════════════════════════╝{Colors.END}
""")
            
            # CPU
            cpu_results = query_prometheus("rate(process_cpu_seconds_total[1m]) * 100")
            cpu = float(cpu_results[0]['value'][1]) if cpu_results else 0
            cpu_bar = "█" * int(cpu / 5) + "░" * max(20 - int(cpu / 5), 0)
            cpu_color = Colors.GREEN if cpu < 50 else Colors.YELLOW if cpu < 80 else Colors.RED
            print(f"  {Colors.CYAN}CPU:{Colors.END}    [{cpu_color}{cpu_bar}{Colors.END}] {cpu:.1f}%")
            
            # Memory
            mem_results = query_prometheus("process_resident_memory_bytes / 1024 / 1024")
            mem = float(mem_results[0]['value'][1]) if mem_results else 0
            mem_bar = "█" * min(int(mem / 25), 20) + "░" * max(20 - int(mem / 25), 0)
            print(f"  {Colors.CYAN}Memory:{Colors.END} [{Colors.BLUE}{mem_bar}{Colors.END}] {mem:.1f} MB")
            
            # Time Series
            ts_results = query_prometheus("prometheus_tsdb_head_series")
            ts = int(float(ts_results[0]['value'][1])) if ts_results else 0
            print(f"  {Colors.CYAN}Time Series:{Colors.END} {Colors.GREEN}{ts:,}{Colors.END}")
            
            # Samples/sec
            samples_results = query_prometheus("rate(prometheus_tsdb_head_samples_appended_total[1m])")
            samples = float(samples_results[0]['value'][1]) if samples_results else 0
            print(f"  {Colors.CYAN}Samples/sec:{Colors.END} {Colors.GREEN}{samples:.1f}{Colors.END}")
            
            # Targets
            targets = get_prometheus_targets()
            up_count = sum(1 for t in targets if t.get('health') == 'up')
            total_count = len(targets)
            print(f"\n  {Colors.CYAN}Scrape Targets:{Colors.END} {Colors.GREEN}{up_count}{Colors.END}/{total_count} up")
            
            for t in targets:
                health = t.get('health', 'unknown')
                job = t.get('labels', {}).get('job', 'unknown')
                color = Colors.GREEN if health == 'up' else Colors.RED
                symbol = "●" if health == 'up' else "○"
                duration = t.get('lastScrapeDuration', 0) * 1000
                print(f"    {color}{symbol} {job}{Colors.END} ({duration:.0f}ms)")
            
            # Docker containers
            result = subprocess.run("docker ps -q | wc -l", shell=True, capture_output=True, text=True)
            containers = result.stdout.strip()
            print(f"\n  {Colors.CYAN}Docker Containers:{Colors.END} {Colors.GREEN}{containers}{Colors.END} running")
            
            # API Health
            try:
                response = requests.get(f"{API_URL}/health", timeout=2)
                if response.status_code == 200:
                    print(f"  {Colors.CYAN}API:{Colors.END} {Colors.GREEN}● Healthy{Colors.END}")
                else:
                    print(f"  {Colors.CYAN}API:{Colors.END} {Colors.RED}○ Unhealthy{Colors.END}")
            except:
                print(f"  {Colors.CYAN}API:{Colors.END} {Colors.RED}○ Unreachable{Colors.END}")
            
            # Database stats
            try:
                result = subprocess.run(
                    "sqlite3 /home/imperium/Imperium/data/imperium.db 'SELECT COUNT(*) FROM intents'",
                    shell=True, capture_output=True, text=True
                )
                intents = result.stdout.strip()
                print(f"  {Colors.CYAN}DB Intents:{Colors.END} {intents}")
            except:
                pass
            
            print(f"\n{Colors.DIM}Refreshing every {REFRESH_INTERVAL}s... Press Ctrl+C to stop{Colors.END}")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped live monitoring.")
        input("Press Enter to continue...")

def live_target_health():
    """Live updating target health"""
    print_info("Starting live target monitoring... Press Ctrl+C to stop")
    time.sleep(1)
    
    try:
        while True:
            clear_screen()
            timestamp = get_timestamp()
            
            print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║          LIVE TARGET HEALTH  [{timestamp}]               ║
╚══════════════════════════════════════════════════════════╝{Colors.END}
""")
            
            targets = get_prometheus_targets()
            
            if not targets:
                print_warning("No targets found. Is Prometheus running?")
            else:
                for t in targets:
                    health = t.get('health', 'unknown')
                    job = t.get('labels', {}).get('job', 'unknown')
                    url = t.get('scrapeUrl', 'N/A')
                    duration = t.get('lastScrapeDuration', 0)
                    error = t.get('lastError', '')
                    
                    color = Colors.GREEN if health == 'up' else Colors.RED
                    symbol = "●" if health == 'up' else "○"
                    
                    print(f"  {color}{symbol} {job}{Colors.END}")
                    print(f"    URL: {url}")
                    print(f"    Duration: {duration*1000:.2f}ms")
                    if error:
                        print(f"    {Colors.RED}Error: {error[:60]}...{Colors.END}")
                    print()
            
            print(f"{Colors.DIM}Refreshing every {REFRESH_INTERVAL}s... Press Ctrl+C to stop{Colors.END}")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped live monitoring.")
        input("Press Enter to continue...")

def live_network_stats():
    """Live network traffic statistics"""
    print_info("Starting live network monitoring... Press Ctrl+C to stop")
    time.sleep(1)
    
    # Get interface
    result = subprocess.run(
        "ip route | grep default | awk '{print $5}' | head -1",
        shell=True, capture_output=True, text=True
    )
    iface = result.stdout.strip() or "wlan0"
    
    prev_rx, prev_tx = 0, 0
    
    try:
        while True:
            clear_screen()
            timestamp = get_timestamp()
            
            print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║       LIVE NETWORK STATS [{iface}]  [{timestamp}]       ║
╚══════════════════════════════════════════════════════════╝{Colors.END}
""")
            
            # Network interface stats
            try:
                with open(f"/sys/class/net/{iface}/statistics/rx_bytes") as f:
                    rx_bytes = int(f.read().strip())
                with open(f"/sys/class/net/{iface}/statistics/tx_bytes") as f:
                    tx_bytes = int(f.read().strip())
                
                # Calculate rates
                rx_rate = (rx_bytes - prev_rx) / REFRESH_INTERVAL if prev_rx > 0 else 0
                tx_rate = (tx_bytes - prev_tx) / REFRESH_INTERVAL if prev_tx > 0 else 0
                prev_rx, prev_tx = rx_bytes, tx_bytes
                
                print(f"  {Colors.CYAN}Interface:{Colors.END} {iface}")
                print(f"  {Colors.CYAN}RX Total:{Colors.END} {rx_bytes / 1024 / 1024:.2f} MB")
                print(f"  {Colors.CYAN}TX Total:{Colors.END} {tx_bytes / 1024 / 1024:.2f} MB")
                print(f"  {Colors.CYAN}RX Rate:{Colors.END} {Colors.GREEN}{rx_rate / 1024:.2f} KB/s{Colors.END}")
                print(f"  {Colors.CYAN}TX Rate:{Colors.END} {Colors.GREEN}{tx_rate / 1024:.2f} KB/s{Colors.END}")
            except:
                print_warning(f"Cannot read stats for {iface}")
            
            # Get TC stats
            print(f"\n  {Colors.CYAN}Traffic Control Classes:{Colors.END}")
            result = subprocess.run(
                f"sudo tc -s class show dev {iface} 2>/dev/null",
                shell=True, capture_output=True, text=True
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('class'):
                        parts = line.split()
                        class_id = parts[2] if len(parts) > 2 else 'unknown'
                        rate = "N/A"
                        for i, p in enumerate(parts):
                            if p == 'rate':
                                rate = parts[i+1] if i+1 < len(parts) else 'N/A'
                                break
                        
                        if '1:10' in class_id:
                            color, label = Colors.GREEN, "HIGH"
                        elif '1:20' in class_id:
                            color, label = Colors.YELLOW, "NORM"
                        else:
                            color, label = Colors.CYAN, "DEF"
                        
                        print(f"    {color}■ {class_id} [{label}]{Colors.END} rate={rate}")
                    elif 'Sent' in line:
                        parts = line.split()
                        bytes_sent = parts[1] if len(parts) > 1 else '0'
                        pkts = parts[3] if len(parts) > 3 else '0'
                        print(f"      Sent: {bytes_sent} bytes, {pkts} pkts")
            else:
                print_info("    No TC rules active (run 'make apply-tc')")
            
            print(f"\n{Colors.DIM}Refreshing every {REFRESH_INTERVAL}s... Press Ctrl+C to stop{Colors.END}")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped live monitoring.")
        input("Press Enter to continue...")

def live_iot_status():
    """Live IoT node status"""
    print_info("Starting live IoT monitoring... Press Ctrl+C to stop")
    time.sleep(1)
    
    try:
        while True:
            clear_screen()
            timestamp = get_timestamp()
            
            print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║          LIVE IOT NODE STATUS  [{timestamp}]            ║
╚══════════════════════════════════════════════════════════╝{Colors.END}
""")
            
            # Get Docker IoT nodes with detailed info
            result = subprocess.run(
                "docker ps --filter 'name=iot-node' --format '{{.Names}}\t{{.Status}}\t{{.RunningFor}}'",
                shell=True, capture_output=True, text=True
            )
            
            if result.stdout:
                nodes = result.stdout.strip().split('\n')
                print(f"  {Colors.CYAN}Simulated IoT Nodes:{Colors.END} {Colors.GREEN}{len(nodes)}{Colors.END} running\n")
                
                # Header
                print(f"  {Colors.BOLD}{'Node Name':<25} {'Status':<15} {'Uptime':<20}{Colors.END}")
                print(f"  {'-'*60}")
                
                for node in sorted(nodes):
                    parts = node.split('\t')
                    name = parts[0] if len(parts) > 0 else 'unknown'
                    status = parts[1] if len(parts) > 1 else 'unknown'
                    uptime = parts[2] if len(parts) > 2 else ''
                    
                    color = Colors.GREEN if 'Up' in status else Colors.RED
                    symbol = "●" if 'Up' in status else "○"
                    print(f"  {color}{symbol}{Colors.END} {name:<24} {status:<15} {uptime:<20}")
                
                # Node description
                print(f"\n  {Colors.YELLOW}What these nodes do:{Colors.END}")
                print(f"  • Generate simulated sensor data (temperature, humidity, pressure)")
                print(f"  • Publish readings to MQTT broker every 5 seconds")
                print(f"  • Respond to control messages (QoS, sampling rate changes)")
                print(f"  • Export Prometheus metrics on ports 8001-8010")
            else:
                print_warning("No IoT nodes running")
                print_info("Start with: docker compose up -d --scale iot-node=10")
            
            # MQTT broker status
            result = subprocess.run(
                "docker ps --filter 'name=mqtt' --format '{{.Names}}\t{{.Status}}'",
                shell=True, capture_output=True, text=True
            )
            mqtt_info = result.stdout.strip()
            if mqtt_info:
                parts = mqtt_info.split('\t')
                mqtt_name = parts[0] if len(parts) > 0 else 'mqtt'
                mqtt_status = parts[1] if len(parts) > 1 else 'unknown'
                mqtt_color = Colors.GREEN if 'Up' in mqtt_status else Colors.RED
                print(f"\n  {Colors.CYAN}MQTT Broker ({mqtt_name}):{Colors.END} {mqtt_color}{mqtt_status}{Colors.END}")
                print(f"    Port: 1883 (unencrypted), 8883 (TLS)")
                print(f"    Topics: iot/+/data, iot/+/control, iot/+/status")
            else:
                print(f"\n  {Colors.CYAN}MQTT Broker:{Colors.END} {Colors.RED}Not running{Colors.END}")
            
            print(f"\n{Colors.DIM}Refreshing every {REFRESH_INTERVAL}s... Press Ctrl+C to stop{Colors.END}")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped live monitoring.")
        input("Press Enter to continue...")

def show_iot_node_details():
    """Show detailed information about IoT nodes and their functions"""
    print_header("IoT Node Simulator Details")
    
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                    SIMULATED IOT NODE ARCHITECTURE                    ║
╚══════════════════════════════════════════════════════════════════════╝{Colors.END}

{Colors.YELLOW}What are these nodes?{Colors.END}
  These are Docker containers running Python scripts that simulate real
  IoT devices (like ESP32 sensors). Each node:
  
  • Generates fake sensor data (temperature, humidity, pressure, battery)
  • Publishes data to MQTT broker on topic: iot/<node-id>/data
  • Listens for control commands on topic: iot/<node-id>/control
  • Reports status on topic: iot/<node-id>/status
  • Exposes Prometheus metrics for monitoring

{Colors.CYAN}Node Configuration:{Colors.END}
  ┌─────────────────────────────────────────────────────────────────┐
  │ Parameter        │ Default Value  │ Description                 │
  ├─────────────────────────────────────────────────────────────────┤
  │ sampling_rate    │ 5 seconds      │ How often data is published │
  │ qos              │ 0              │ MQTT QoS level (0, 1, or 2) │
  │ priority         │ normal         │ Traffic priority            │
  │ enabled          │ true           │ Whether node is active      │
  └─────────────────────────────────────────────────────────────────┘

{Colors.GREEN}Sample Data Generated:{Colors.END}
  {{
    "node_id": "node-1",
    "timestamp": "2026-01-29T10:30:00",
    "temperature": 22.5,    // °C (range: 15-25)
    "humidity": 48.3,       // % (range: 40-60)
    "pressure": 1015.2,     // hPa (range: 993-1033)
    "battery": 94.5         // % (range: 80-100)
  }}

{Colors.YELLOW}How Imperium Controls These Nodes:{Colors.END}
  1. User submits intent: "reduce latency for node-1"
  2. Intent Parser extracts: device=node-1, action=reduce_latency
  3. Policy Engine generates: {{qos: 2, priority: high}}
  4. Device Enforcer publishes to MQTT: iot/node-1/control
  5. Node receives message and updates its configuration
  6. Feedback loop monitors if latency target is met
""")
    
    # Show running nodes
    print(f"\n{Colors.CYAN}Currently Running Nodes:{Colors.END}")
    result = subprocess.run(
        "docker ps --filter 'name=iot-node' --format '{{.Names}}'",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        nodes = sorted(result.stdout.strip().split('\n'))
        for i, node in enumerate(nodes, 1):
            print(f"  {Colors.GREEN}●{Colors.END} {node}")
    else:
        print(f"  {Colors.RED}No nodes running{Colors.END}")

def iot_node_menu():
    """IoT Node management menu"""
    while True:
        clear_screen()
        print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║               IOT NODE MANAGEMENT                         ║
╠══════════════════════════════════════════════════════════╣{Colors.END}
{Colors.CYAN}  Information:{Colors.END}
    1. Show Node Details & Architecture
    2. List Running Nodes (Simulated + ESP32)
    3. View Node Logs
    
{Colors.CYAN}  Node Control:{Colors.END}
    4. Send Control Message (via MQTT)
    5. View Recent MQTT Messages
    6. Check Node Metrics (Prometheus)
    
{Colors.GREEN}  Live Monitoring:{Colors.END}
    7. Live Node Status (auto-refresh)
    8. Simulate Load Test
    
{Colors.CYAN}  Management:{Colors.END}
    9. Start More Nodes
   10. Stop All Nodes
    
{Colors.YELLOW}   b. Back to Main Menu{Colors.END}
{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════╝{Colors.END}
""")
        
        choice = input(f"{Colors.CYAN}Select option:{Colors.END} ").strip().lower()
        
        if choice == 'b':
            break
        elif choice == '1':
            show_iot_node_details()
            input("\nPress Enter to continue...")
        elif choice == '2':
            print_header("Running IoT Nodes")
            
            # Show simulated Docker nodes
            result = subprocess.run(
                "docker ps --filter 'name=iot-node' --format 'table {{.Names}}\t{{.Status}}'",
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                print(f"{Colors.CYAN}Simulated Nodes (Docker):{Colors.END}")
                print(result.stdout)
            else:
                print_warning("No simulated nodes running")
            
            # Check ESP32 hardware node
            print(f"\n{Colors.CYAN}Hardware Nodes:{Colors.END}")
            try:
                response = requests.get("http://10.218.189.218:8080/metrics", timeout=2)
                if response.status_code == 200:
                    print(f"  {Colors.GREEN}● esp32-audio-1{Colors.END} - ONLINE (10.218.189.218:8080)")
                else:
                    print(f"  {Colors.RED}○ esp32-audio-1{Colors.END} - HTTP {response.status_code}")
            except:
                print(f"  {Colors.RED}○ esp32-audio-1{Colors.END} - OFFLINE")
            
            input("\nPress Enter to continue...")
        elif choice == '3':
            print_header("Node Logs")
            print("Select a node to view logs:")
            result = subprocess.run(
                "docker ps --filter 'name=iot-node' --format '{{.Names}}'",
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                nodes = sorted(result.stdout.strip().split('\n'))
                for i, node in enumerate(nodes, 1):
                    print(f"  {i}. {node}")
                
                choice_node = input(f"\n{Colors.CYAN}Enter number (or 'all' for all nodes):{Colors.END} ").strip()
                if choice_node == 'all':
                    for node in nodes[:3]:
                        print(f"\n{Colors.YELLOW}=== {node} ==={Colors.END}")
                        os.system(f"docker logs {node} --tail 10 2>&1")
                elif choice_node.isdigit() and 1 <= int(choice_node) <= len(nodes):
                    node = nodes[int(choice_node) - 1]
                    print(f"\n{Colors.YELLOW}=== Logs for {node} ==={Colors.END}")
                    os.system(f"docker logs {node} --tail 30 2>&1")
            else:
                print_warning("No nodes running")
            input("\nPress Enter to continue...")
        elif choice == '4':
            send_mqtt_control_message()
            input("\nPress Enter to continue...")
        elif choice == '5':
            print_header("Recent MQTT Messages")
            print_info("Subscribing to MQTT for 5 seconds...")
            result = subprocess.run(
                "timeout 5 docker exec imperium-mqtt mosquitto_sub -t 'iot/#' -v 2>/dev/null || echo 'MQTT not available or no messages'",
                shell=True, capture_output=True, text=True
            )
            if result.stdout:
                print(result.stdout[:2000])
            else:
                print_warning("No messages received (nodes may not be publishing)")
            input("\nPress Enter to continue...")
        elif choice == '6':
            print_header("Node Prometheus Metrics")
            
            # Check ESP32 first
            print(f"\n{Colors.CYAN}ESP32 Hardware Node:{Colors.END}")
            try:
                response = requests.get("http://10.218.189.218:8080/metrics", timeout=2)
                if response.status_code == 200:
                    print(f"  {Colors.GREEN}● esp32-audio-1{Colors.END} - http://10.218.189.218:8080/metrics")
                    # Parse and show key metrics
                    for line in response.text.split('\n'):
                        if 'audio_sample_rate_hz{' in line and not line.startswith('#'):
                            val = line.split('}')[1].strip()
                            print(f"    Sample Rate: {val} Hz")
                        elif 'audio_gain_multiplier{' in line and not line.startswith('#'):
                            val = line.split('}')[1].strip()
                            print(f"    Audio Gain: {val}x")
                        elif 'telemetry_publish_interval_ms{' in line and not line.startswith('#'):
                            val = line.split('}')[1].strip()
                            print(f"    Publish Interval: {float(val)/1000}s")
                        elif 'mqtt_qos_level{' in line and not line.startswith('#'):
                            val = line.split('}')[1].strip()
                            print(f"    QoS Level: {val}")
                        elif 'audio_frames_captured_total{' in line and not line.startswith('#'):
                            val = line.split('}')[1].strip()
                            print(f"    Frames Captured: {val}")
                else:
                    print(f"  {Colors.RED}○ esp32-audio-1{Colors.END} - OFFLINE")
            except:
                print(f"  {Colors.RED}○ esp32-audio-1{Colors.END} - UNREACHABLE")
            
            # Check simulated nodes
            print(f"\n{Colors.CYAN}Simulated IoT Nodes:{Colors.END}")
            print_info("Each node exposes metrics on port 8001-8010")
            for port in range(8001, 8011):
                try:
                    response = requests.get(f"http://localhost:{port}/metrics", timeout=1)
                    if response.status_code == 200:
                        print(f"  {Colors.GREEN}●{Colors.END} Port {port}: Available")
                except:
                    print(f"  {Colors.RED}○{Colors.END} Port {port}: Not reachable")
            input("\nPress Enter to continue...")
        elif choice == '7':
            live_iot_status()
        elif choice == '8':
            print_header("Load Test Simulation")
            print_warning("This will submit multiple intents rapidly to test the system.")
            confirm = input(f"{Colors.CYAN}Continue? (y/n):{Colors.END} ").strip().lower()
            if confirm == 'y':
                simulate_load_test()
            input("\nPress Enter to continue...")
        elif choice == '9':
            print_header("Start More Nodes")
            count = input(f"{Colors.CYAN}How many nodes to start (1-20):{Colors.END} ").strip()
            if count.isdigit() and 1 <= int(count) <= 20:
                print_info(f"Starting {count} nodes...")
                os.system(f"cd /home/imperium/Imperium && docker compose up -d --scale iot-node={count}")
                print_success(f"Started {count} nodes")
            else:
                print_error("Invalid number")
            input("\nPress Enter to continue...")
        elif choice == '10':
            print_header("Stop All Nodes")
            confirm = input(f"{Colors.CYAN}Stop all IoT nodes? (y/n):{Colors.END} ").strip().lower()
            if confirm == 'y':
                os.system("docker compose stop iot-node")
                print_success("All IoT nodes stopped")
            input("\nPress Enter to continue...")

def send_mqtt_control_message():
    """Send control message to IoT node via MQTT"""
    print_header("Send MQTT Control Message")
    
    # List available nodes (simulated + ESP32)
    result = subprocess.run(
        "docker ps --filter 'name=iot-node' --format '{{.Names}}'",
        shell=True, capture_output=True, text=True
    )
    
    nodes = []
    if result.stdout:
        nodes = sorted(result.stdout.strip().split('\n'))
    
    # Add ESP32 if online
    esp32_online = False
    try:
        resp = requests.get("http://10.218.189.218:8080/metrics", timeout=2)
        if resp.status_code == 200:
            esp32_online = True
            nodes.append("esp32-audio-1")
    except:
        pass
    
    if not nodes:
        print_warning("No IoT nodes running")
        return
    
    print(f"{Colors.CYAN}Available nodes:{Colors.END}")
    for i, node in enumerate(nodes, 1):
        if node.startswith('esp32'):
            status = f"{Colors.GREEN}● ONLINE{Colors.END}" if esp32_online else f"{Colors.RED}○ OFFLINE{Colors.END}"
            print(f"  {i}. {node} (ESP32 Hardware) {status}")
        else:
            node_id = node.replace('imperium-iot-', '')
            print(f"  {i}. {node_id}")
    
    print(f"\n{Colors.CYAN}Example control messages (Simulated Nodes):{Colors.END}")
    print('  • {"qos": 2}                    - Set QoS level to 2')
    print('  • {"sampling_rate": 10}         - Set sampling rate to 10s')
    print('  • {"priority": "high"}          - Set high priority')
    print('  • {"enabled": false}            - Disable node')
    print(f"\n{Colors.CYAN}ESP32 Audio Node Commands:{Colors.END}")
    print('  • {"command":"SET_SAMPLE_RATE","sample_rate":48000}')
    print('  • {"command":"SET_AUDIO_GAIN","gain":2.5}')
    print('  • {"command":"SET_PUBLISH_INTERVAL","interval_ms":5000}')
    print('  • {"command":"SET_QOS","qos":2}')
    print('  • {"command":"RESET"}')
    
    node_num = input(f"\n{Colors.CYAN}Select node number:{Colors.END} ").strip()
    if not node_num.isdigit() or not 1 <= int(node_num) <= len(nodes):
        print_error("Invalid selection")
        return
    
    node = nodes[int(node_num) - 1]
    
    # Handle ESP32 vs simulated nodes differently
    if node.startswith('esp32'):
        node_id = node
    else:
        node_id = node.replace('imperium-iot-', '')
    
    message = input(f"{Colors.CYAN}Enter JSON message:{Colors.END} ").strip()
    if not message:
        message = '{"qos": 2}'
    
    # Send via mosquitto_pub
    topic = f"iot/{node_id}/control"
    cmd = f"docker exec imperium-mqtt-1 mosquitto_pub -t '{topic}' -m '{message}'"
    
    print(f"\n{Colors.YELLOW}Sending to topic: {topic}{Colors.END}")
    print(f"{Colors.YELLOW}Message: {message}{Colors.END}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print_success("Message sent successfully!")
        if node.startswith('esp32'):
            print_info("Wait 3 seconds, then check metrics: http://10.218.189.218:8080/metrics")
        else:
            print_info("Check node logs to see if it was received")
    else:
        print_error(f"Failed to send: {result.stderr}")

def simulate_load_test():
    """Simulate load test by submitting multiple intents"""
    global TOKEN
    if not TOKEN:
        login()
    
    test_intents = [
        "prioritize node-1 and node-2",
        "limit bandwidth to 100KB/s for node-3",
        "reduce latency to 20ms for node-4",
        "set QoS level 2 for node-5 and node-6",
        "prioritize node-7 through node-10",
    ]
    
    print(f"\n{Colors.CYAN}Submitting {len(test_intents)} intents...{Colors.END}\n")
    
    for i, intent in enumerate(test_intents, 1):
        start = time.time()
        try:
            response = requests.post(
                f"{API_URL}/api/v1/intents",
                headers={"Authorization": f"Bearer {TOKEN}"},
                json={"description": intent},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            if response.status_code in [200, 201]:
                print(f"  {Colors.GREEN}✓{Colors.END} Intent {i}: {elapsed:.0f}ms")
            else:
                print(f"  {Colors.RED}✗{Colors.END} Intent {i}: Failed - {response.status_code}")
        except Exception as e:
            print(f"  {Colors.RED}✗{Colors.END} Intent {i}: Error - {e}")
        time.sleep(0.2)  # Small delay between requests
    
    print(f"\n{Colors.GREEN}Load test complete!{Colors.END}")

def live_full_dashboard():
    """Combined live dashboard with all metrics"""
    print_info("Starting full dashboard... Press Ctrl+C to stop")
    time.sleep(1)
    
    result = subprocess.run(
        "ip route | grep default | awk '{print $5}' | head -1",
        shell=True, capture_output=True, text=True
    )
    iface = result.stdout.strip() or "wlan0"
    
    try:
        while True:
            clear_screen()
            timestamp = get_timestamp()
            
            print(f"{Colors.HEADER}{Colors.BOLD}═══════════════════ IMPERIUM LIVE DASHBOARD [{timestamp}] ═══════════════════{Colors.END}\n")
            
            # Row 1: System metrics
            print(f"{Colors.CYAN}┌─ SYSTEM ─────────────────────────────┐ ┌─ PROMETHEUS ────────────────────────┐{Colors.END}")
            
            # Get all data
            result = subprocess.run("docker ps -q | wc -l", shell=True, capture_output=True, text=True)
            containers = result.stdout.strip()
            
            result = subprocess.run("free -m | awk '/^Mem:/ {print $3\"/\"$2}'", shell=True, capture_output=True, text=True)
            memory = result.stdout.strip()
            
            targets = get_prometheus_targets()
            up_count = sum(1 for t in targets if t.get('health') == 'up')
            metrics_count = get_prometheus_metrics_count()
            
            ts_results = query_prometheus("prometheus_tsdb_head_series")
            ts = int(float(ts_results[0]['value'][1])) if ts_results else 0
            
            print(f"│ Containers: {Colors.GREEN}{containers:>4}{Colors.END} running           │ │ Targets: {Colors.GREEN}{up_count}{Colors.END}/{len(targets)} up                     │")
            print(f"│ Memory: {memory:>15}        │ │ Metrics: {Colors.GREEN}{metrics_count:>5}{Colors.END}                      │")
            print(f"│ Interface: {iface:>14}         │ │ Series: {Colors.GREEN}{ts:>6,}{Colors.END}                     │")
            
            # API status
            try:
                response = requests.get(f"{API_URL}/health", timeout=1)
                api_status = f"{Colors.GREEN}● Healthy{Colors.END}" if response.status_code == 200 else f"{Colors.RED}○ Error{Colors.END}"
            except:
                api_status = f"{Colors.RED}○ Down{Colors.END}"
            
            print(f"│ API: {api_status:>30} │ │                                     │")
            print(f"{Colors.CYAN}└──────────────────────────────────────┘ └─────────────────────────────────────┘{Colors.END}")
            
            # Row 2: IoT nodes
            print(f"\n{Colors.CYAN}┌─ IOT NODES ─────────────────────────────────────────────────────────────────┐{Colors.END}")
            result = subprocess.run(
                "docker ps --filter 'name=iot-node' --format '{{.Names}}'",
                shell=True, capture_output=True, text=True
            )
            nodes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            node_str = "  ".join([f"{Colors.GREEN}●{Colors.END}" for _ in nodes[:10]])
            if len(nodes) > 10:
                node_str += f"  +{len(nodes)-10} more"
            print(f"│ {node_str:74} │")
            print(f"│ Total: {Colors.GREEN}{len(nodes)}{Colors.END} nodes active                                                      │")
            print(f"{Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}")
            
            # Row 3: Database & Intents
            print(f"\n{Colors.CYAN}┌─ DATABASE ──────────────────────────────────────────────────────────────────┐{Colors.END}")
            try:
                result = subprocess.run(
                    "sqlite3 /home/imperium/Imperium/data/imperium.db 'SELECT COUNT(*) FROM intents'",
                    shell=True, capture_output=True, text=True
                )
                intent_count = result.stdout.strip()
                result = subprocess.run(
                    "sqlite3 /home/imperium/Imperium/data/imperium.db 'SELECT COUNT(*) FROM policies'",
                    shell=True, capture_output=True, text=True
                )
                policy_count = result.stdout.strip()
                print(f"│ Intents: {Colors.GREEN}{intent_count:>4}{Colors.END}    Policies: {Colors.GREEN}{policy_count:>4}{Colors.END}                                           │")
            except:
                print(f"│ Database unavailable                                                        │")
            print(f"{Colors.CYAN}└─────────────────────────────────────────────────────────────────────────────┘{Colors.END}")
            
            print(f"\n{Colors.DIM}Refreshing every {REFRESH_INTERVAL}s... Press Ctrl+C to stop{Colors.END}")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nStopped dashboard.")
        input("Press Enter to continue...")

def show_network_status():
    """Show TC network rules"""
    print_header("Network Enforcement Status")
    
    # Get active interface
    result = subprocess.run(
        "ip route | grep default | awk '{print $5}' | head -1",
        shell=True, capture_output=True, text=True
    )
    iface = result.stdout.strip() or "wlan0"
    print_info(f"Active interface: {iface}")
    
    # Show qdisc
    print(f"\n{Colors.CYAN}Traffic Control Qdisc:{Colors.END}")
    os.system(f"sudo tc qdisc show dev {iface}")
    
    # Show classes
    print(f"\n{Colors.CYAN}Traffic Classes:{Colors.END}")
    os.system(f"sudo tc class show dev {iface}")
    
    # Show stats
    print(f"\n{Colors.CYAN}Traffic Statistics:{Colors.END}")
    os.system(f"sudo tc -s class show dev {iface} 2>/dev/null | head -20")

def show_docker_status():
    """Show Docker container status"""
    print_header("Docker Container Status")
    
    # Summary
    result = subprocess.run("docker ps -q | wc -l", shell=True, capture_output=True, text=True)
    running = result.stdout.strip()
    result = subprocess.run("docker ps -aq | wc -l", shell=True, capture_output=True, text=True)
    total = result.stdout.strip()
    
    print(f"  {Colors.CYAN}Running:{Colors.END} {Colors.GREEN}{running}{Colors.END} / {total} total\n")
    
    # Categorized display
    print(f"  {Colors.YELLOW}Infrastructure:{Colors.END}")
    result = subprocess.run(
        "docker ps --filter 'name=mqtt' --filter 'name=prometheus' --filter 'name=grafana' --format '    {{.Names}}: {{.Status}}'",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            color = Colors.GREEN if 'Up' in line else Colors.RED
            print(f"  {color}●{Colors.END}{line}")
    
    print(f"\n  {Colors.YELLOW}IoT Nodes:{Colors.END}")
    result = subprocess.run(
        "docker ps --filter 'name=iot-node' --format '{{.Names}}'",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        nodes = result.stdout.strip().split('\n')
        # Show as grid
        node_line = "    "
        for i, node in enumerate(sorted(nodes)):
            short_name = node.replace('imperium-iot-', '')
            node_line += f"{Colors.GREEN}●{Colors.END}{short_name} "
            if (i + 1) % 5 == 0:
                print(node_line)
                node_line = "    "
        if node_line.strip():
            print(node_line)
        print(f"\n    Total IoT nodes: {Colors.GREEN}{len(nodes)}{Colors.END}")
    else:
        print(f"    {Colors.RED}No IoT nodes running{Colors.END}")
    
    # Show ports (only for services with exposed ports)
    print(f"\n  {Colors.YELLOW}Published Ports:{Colors.END}")
    result = subprocess.run(
        "docker ps --format '{{.Names}}\t{{.Ports}}'",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            parts = line.split('\t')
            name = parts[0][:18] if len(parts) > 0 else ''
            ports = parts[1] if len(parts) > 1 else ''
            if ports and ('0.0.0.0' in ports or ':::' in ports):
                # Extract just the port numbers
                port_nums = []
                for p in ports.split(', '):
                    if '0.0.0.0:' in p:
                        port_nums.append(p.split('0.0.0.0:')[1].split('->')[0])
                port_display = ', '.join(sorted(set(port_nums)))
                print(f"    {name:<18} ports: {Colors.CYAN}{port_display}{Colors.END}")

def show_system_status():
    """Show overall system status"""
    print_header("System Status Overview")
    
    # API Status
    print(f"{Colors.CYAN}┌─ IMPERIUM API ────────────────────────────────────────────┐{Colors.END}")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"│ Status: {Colors.GREEN}● Running{Colors.END}                                       │")
            print(f"│ URL: {API_URL:<48} │")
            features = data.get('features', {})
            print(f"│ Auth: {'✓' if features.get('authentication') else '✗'}  DB: {'✓' if features.get('database') else '✗'}  Rate Limit: {'✓' if features.get('rate_limiting') else '✗'}                        │")
        else:
            print(f"│ Status: {Colors.RED}○ Error ({response.status_code}){Colors.END}                              │")
    except Exception as e:
        print(f"│ Status: {Colors.RED}○ Unreachable{Colors.END}                                   │")
    print(f"{Colors.CYAN}└───────────────────────────────────────────────────────────┘{Colors.END}")
    
    # Docker status
    print(f"\n{Colors.CYAN}┌─ DOCKER SERVICES ─────────────────────────────────────────┐{Colors.END}")
    result = subprocess.run(
        "docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'mqtt|prom|grafana|iot' | head -6",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n')[:6]:
            parts = line.split('\t')
            name = parts[0][:20] if len(parts) > 0 else 'unknown'
            status = parts[1][:25] if len(parts) > 1 else 'unknown'
            color = Colors.GREEN if 'Up' in status else Colors.RED
            print(f"│ {color}●{Colors.END} {name:<20} {status:<30} │")
    
    result = subprocess.run("docker ps -q | wc -l", shell=True, capture_output=True, text=True)
    total = result.stdout.strip()
    print(f"│ Total containers: {Colors.GREEN}{total}{Colors.END}                                      │")
    print(f"{Colors.CYAN}└───────────────────────────────────────────────────────────┘{Colors.END}")
    
    # Resources
    print(f"\n{Colors.CYAN}┌─ SYSTEM RESOURCES ────────────────────────────────────────┐{Colors.END}")
    result = subprocess.run("free -h | awk '/^Mem:/ {print $3\"/\"$2}'", shell=True, capture_output=True, text=True)
    memory = result.stdout.strip()
    result = subprocess.run("df -h / | awk 'NR==2 {print $3\"/\"$2}'", shell=True, capture_output=True, text=True)
    disk = result.stdout.strip()
    result = subprocess.run("uptime -p 2>/dev/null || uptime | awk -F'up' '{print $2}' | awk -F',' '{print $1}'", shell=True, capture_output=True, text=True)
    uptime_str = result.stdout.strip()
    
    print(f"│ Memory: {memory:<15}  Disk: {disk:<15}          │")
    print(f"│ Uptime: {uptime_str:<45} │")
    print(f"{Colors.CYAN}└───────────────────────────────────────────────────────────┘{Colors.END}")
    
    # Database
    print(f"\n{Colors.CYAN}┌─ DATABASE ────────────────────────────────────────────────┐{Colors.END}")
    db_path = "/home/imperium/Imperium/data/imperium.db"
    if os.path.exists(db_path):
        result = subprocess.run(f"sqlite3 {db_path} 'SELECT COUNT(*) FROM intents'", shell=True, capture_output=True, text=True)
        intents = result.stdout.strip()
        result = subprocess.run(f"sqlite3 {db_path} 'SELECT COUNT(*) FROM policies'", shell=True, capture_output=True, text=True)
        policies = result.stdout.strip()
        result = subprocess.run(f"ls -lh {db_path} | awk '{{print $5}}'", shell=True, capture_output=True, text=True)
        size = result.stdout.strip()
        print(f"│ Intents: {Colors.GREEN}{intents:>4}{Colors.END}    Policies: {Colors.GREEN}{policies:>4}{Colors.END}    Size: {size:<10}      │")
    else:
        print(f"│ Status: {Colors.RED}Database not found{Colors.END}                           │")
    print(f"{Colors.CYAN}└───────────────────────────────────────────────────────────┘{Colors.END}")
    
    # Quick links
    print(f"\n{Colors.CYAN}┌─ QUICK LINKS ─────────────────────────────────────────────┐{Colors.END}")
    print(f"│ API:        http://localhost:5000                        │")
    print(f"│ Prometheus: http://localhost:9090                        │")
    print(f"│ Grafana:    http://localhost:3000  (admin/admin)         │")
    print(f"│ MQTT:       localhost:1883                               │")
    print(f"{Colors.CYAN}└───────────────────────────────────────────────────────────┘{Colors.END}")

def run_demo_sequence():
    """Run the full demo sequence automatically"""
    print_header("Running Full Demo Sequence")
    
    # Step 1: Health check
    print(f"\n{Colors.BOLD}Step 1: Health Check{Colors.END}")
    check_health()
    input("\nPress Enter to continue...")
    
    # Step 2: Login
    print(f"\n{Colors.BOLD}Step 2: Authentication{Colors.END}")
    login()
    input("\nPress Enter to continue...")
    
    # Step 3: Submit intents
    print(f"\n{Colors.BOLD}Step 3: Submit Demo Intents{Colors.END}")
    demo_intents = [
        "prioritize node-1 and limit bandwidth to 50KB/s for node-2",
        "reduce latency to 20ms for node-3 and node-4",
        "set QoS level 2 for node-5 through node-10"
    ]
    
    for i, intent in enumerate(demo_intents, 1):
        print(f"\n{Colors.YELLOW}Intent {i}:{Colors.END} {intent}")
        submit_intent(intent)
        input("\nPress Enter to continue...")
    
    # Step 4: List intents
    print(f"\n{Colors.BOLD}Step 4: View All Intents{Colors.END}")
    list_intents()
    input("\nPress Enter to continue...")
    
    # Step 5: Network status
    print(f"\n{Colors.BOLD}Step 5: Network Enforcement{Colors.END}")
    show_network_status()
    
    print_success("\nDemo sequence complete!")

# ============== Predefined Intents ==============

EXAMPLE_INTENTS = [
    # Simulated IoT Node Intents
    "prioritize node-1",
    "limit bandwidth to 100KB/s for node-2",
    "reduce latency to 10ms for node-3",
    "set QoS level 2 for node-4",
    "prioritize node-1 through node-5",
    "limit bandwidth to 50KB/s for node-6 and node-7",
    "reduce latency for node-8 and node-9",
    "set high priority for node-10",
    
    # ESP32 Hardware Node Intents
    "set sample rate to 48000 hz for esp32-audio-1",
    "set audio gain to 2.5 for esp32-audio-1",
    "set publish interval to 5 seconds for esp32-audio-1",
    "set sample rate to 8000 hz for esp32-audio-1",
    "set audio gain to 0.5 for esp32-audio-1",
    "set QoS level 2 for esp32-audio-1",
]

def submit_example_intent():
    """Show example intents and submit selected one"""
    print_header("Example Intents")
    
    for i, intent in enumerate(EXAMPLE_INTENTS, 1):
        print(f"  {i}. {intent}")
    
    print(f"\n  0. Enter custom intent")
    print(f"  q. Back to main menu")
    
    choice = input(f"\n{Colors.CYAN}Select intent (1-{len(EXAMPLE_INTENTS)}):{Colors.END} ").strip()
    
    if choice.lower() == 'q':
        return
    elif choice == '0':
        custom = input(f"{Colors.CYAN}Enter your intent:{Colors.END} ").strip()
        if custom:
            submit_intent(custom)
    elif choice.isdigit() and 1 <= int(choice) <= len(EXAMPLE_INTENTS):
        submit_intent(EXAMPLE_INTENTS[int(choice) - 1])
    else:
        print_error("Invalid selection")

# ============== Main Menu ==============

def main_menu():
    """Display main menu"""
    global TOKEN
    
    while True:
        clear_screen()
        print(f"""
{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════╗
║       IMPERIUM IBN - INTERACTIVE DEMO (v3)               ║
╠══════════════════════════════════════════════════════════╣{Colors.END}
{Colors.CYAN}  Authentication:{Colors.END}
    1. Login                    2. Check API Health
    
{Colors.CYAN}  Intent Management:{Colors.END}
    3. Submit Intent (Examples) 4. Submit Custom Intent
    5. List All Intents         6. List Policies
    
{Colors.CYAN}  System Status:{Colors.END}
    7. Docker Containers        8. Network (TC) Status
    9. System Overview
    
{Colors.GREEN}  Monitoring:{Colors.END}
   10. Prometheus Menu         11. Grafana Menu
   
{Colors.GREEN}  IoT Nodes:{Colors.END}
   12. IoT Node Menu           13. Live IoT Status
   
{Colors.GREEN}  Live Dashboards:{Colors.END}
   14. Live System Metrics     15. Live Network Stats
   16. Full Dashboard
    
{Colors.CYAN}  Demo:{Colors.END}
   17. Run Full Demo (Automated)
    
{Colors.YELLOW}   q. Quit{Colors.END}
{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════╝{Colors.END}
""")
        
        # Show login and system status
        if TOKEN:
            print(f"{Colors.GREEN}  ● Logged in{Colors.END}", end="")
        else:
            print(f"{Colors.RED}  ○ Not logged in{Colors.END}", end="")
        
        # Quick status
        result = subprocess.run("docker ps -q | wc -l", shell=True, capture_output=True, text=True)
        containers = result.stdout.strip()
        print(f"  |  {Colors.CYAN}Containers:{Colors.END} {containers}", end="")
        
        try:
            response = requests.get(f"{API_URL}/health", timeout=1)
            if response.status_code == 200:
                print(f"  |  {Colors.GREEN}API: ●{Colors.END}")
            else:
                print(f"  |  {Colors.RED}API: ○{Colors.END}")
        except:
            print(f"  |  {Colors.RED}API: ○{Colors.END}")
        
        choice = input(f"\n{Colors.CYAN}Select option:{Colors.END} ").strip().lower()
        
        if choice == 'q':
            print("\nGoodbye!")
            break
        elif choice == '1':
            print_header("Login")
            username = input("Username [admin]: ").strip() or "admin"
            password = input("Password [admin]: ").strip() or "admin"
            login(username, password)
            input("\nPress Enter to continue...")
        elif choice == '2':
            print_header("API Health Check")
            check_health()
            input("\nPress Enter to continue...")
        elif choice == '3':
            submit_example_intent()
            input("\nPress Enter to continue...")
        elif choice == '4':
            print_header("Custom Intent")
            if not TOKEN:
                print_info("Logging in first...")
                login()
            print(f"\n{Colors.DIM}Simulated IoT Nodes (node-1 through node-10):{Colors.END}")
            print(f"  - prioritize node-1")
            print(f"  - limit bandwidth to 50KB/s for node-2")
            print(f"  - reduce latency to 10ms for node-3")
            print(f"  - set QoS level 2 for node-4 and node-5")
            print(f"\n{Colors.DIM}ESP32 Audio Node (esp32-audio-1):{Colors.END}")
            print(f"  - set sample rate to 48000 hz for esp32-audio-1")
            print(f"  - set audio gain to 2.5 for esp32-audio-1")
            print(f"  - set telemetry rate to 5 seconds for esp32-audio-1")
            print(f"  - amplify audio by 3x for esp32-audio-1")
            print(f"  - report telemetry every 2 seconds for esp32-audio-1")
            description = input(f"\n{Colors.CYAN}Enter intent description:{Colors.END} ").strip()
            if description:
                submit_intent(description)
            input("\nPress Enter to continue...")
        elif choice == '5':
            print_header("All Intents")
            list_intents()
            input("\nPress Enter to continue...")
        elif choice == '6':
            print_header("All Policies")
            list_policies()
            input("\nPress Enter to continue...")
        elif choice == '7':
            show_docker_status()
            input("\nPress Enter to continue...")
        elif choice == '8':
            show_network_status()
            input("\nPress Enter to continue...")
        elif choice == '9':
            show_system_status()
            input("\nPress Enter to continue...")
        elif choice == '10':
            prometheus_menu()
        elif choice == '11':
            grafana_menu()
        elif choice == '12':
            iot_node_menu()
        elif choice == '13':
            live_iot_status()
        elif choice == '14':
            live_system_metrics()
        elif choice == '15':
            live_network_stats()
        elif choice == '16':
            live_full_dashboard()
        elif choice == '17':
            run_demo_sequence()
            input("\nPress Enter to continue...")
        else:
            print_error("Invalid option")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    # Change to project directory
    os.chdir("/home/imperium/Imperium")
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
