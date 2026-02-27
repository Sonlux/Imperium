#!/usr/bin/env python3
"""
Imperium Prometheus Metrics Exporter

Exports controller-level and per-device network metrics so Prometheus
can scrape them.  Runs a standalone HTTP server on port 8000 (separate
from the Flask API on 5000).

Exported metrics
────────────────
  ibs_tc_bandwidth_bytes_total   – bytes sent through each device's tc class
  ibs_tc_packets_total           – packets sent
  ibs_tc_dropped_total           – packets dropped by tc
  ibs_tc_overlimits_total        – tc overlimit events
  ibs_tc_configured_rate_bps     – configured HTB rate (bits/sec)
  ibs_tc_configured_delay_ms     – configured netem delay
  ibs_tc_configured_priority     – configured HTB prio
  ibs_policy_active              – number of active network policies
  ibs_intent_active              – number of active intents
  ibs_policy_enforcement_total   – total enforcement operations counter
  ibs_policy_enforcement_latency_seconds – histogram of enforcement latency
"""

import logging
import re
import threading
import time
from typing import Optional

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)

logger = logging.getLogger(__name__)

# ── Single shared registry ───────────────────────────────────────────────
REGISTRY = CollectorRegistry()

# Per-device tc stats (updated by polling thread)
tc_bytes = Gauge(
    "ibs_tc_bandwidth_bytes_total",
    "Total bytes sent through device tc class",
    ["device"],
    registry=REGISTRY,
)
tc_packets = Gauge(
    "ibs_tc_packets_total",
    "Total packets sent through device tc class",
    ["device"],
    registry=REGISTRY,
)
tc_dropped = Gauge(
    "ibs_tc_dropped_total",
    "Packets dropped by tc for device",
    ["device"],
    registry=REGISTRY,
)
tc_overlimits = Gauge(
    "ibs_tc_overlimits_total",
    "TC overlimit events for device",
    ["device"],
    registry=REGISTRY,
)

# Configured policy values (set when a policy is applied)
tc_rate_bps = Gauge(
    "ibs_tc_configured_rate_bps",
    "Configured HTB rate in bits/sec",
    ["device"],
    registry=REGISTRY,
)
tc_delay_ms = Gauge(
    "ibs_tc_configured_delay_ms",
    "Configured netem delay in milliseconds",
    ["device"],
    registry=REGISTRY,
)
tc_priority = Gauge(
    "ibs_tc_configured_priority",
    "Configured HTB priority (lower = higher priority)",
    ["device"],
    registry=REGISTRY,
)

# System-level gauges
policy_active = Gauge(
    "ibs_policy_active",
    "Number of active network policies",
    registry=REGISTRY,
)
intent_active = Gauge(
    "ibs_intent_active",
    "Number of active intents",
    registry=REGISTRY,
)

# Enforcement counters
enforcement_total = Counter(
    "ibs_policy_enforcement_total",
    "Total network enforcement operations",
    ["policy_type", "status"],
    registry=REGISTRY,
)
enforcement_latency = Histogram(
    "ibs_policy_enforcement_latency_seconds",
    "Time to apply a network policy",
    ["policy_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=REGISTRY,
)

# ── Controller-side device metrics ────────────────────────────────────────
# These track the *last command sent* by the device enforcer, so Grafana
# can visualise intent-driven changes even when the firmware doesn't
# expose a /metrics gauge for that setting.

device_enforcement_total = Counter(
    "ibs_device_enforcement_total",
    "Total device enforcement operations",
    ["policy_type", "device", "status"],
    registry=REGISTRY,
)

# Camera settings (controller-side mirror)
cam_resolution = Gauge(
    "ibs_cam_resolution_index",
    "Camera resolution as framesize index (0=QQVGA..13=UXGA)",
    ["device"],
    registry=REGISTRY,
)
cam_brightness = Gauge(
    "ibs_cam_brightness",
    "Camera brightness setting (-2..+2)",
    ["device"],
    registry=REGISTRY,
)
cam_enabled = Gauge(
    "ibs_cam_enabled",
    "Camera enabled state (1=on 0=off)",
    ["device"],
    registry=REGISTRY,
)

# Map resolution names to numeric indices for Grafana
RESOLUTION_INDEX = {
    'QQVGA': 0, 'QVGA': 3, 'CIF': 4, 'VGA': 6, 'SVGA': 7,
    'XGA': 8, 'SXGA': 9, 'UXGA': 10, 'HD': 8, 'QXGA': 11,
}


def _parse_rate_to_bps(rate_str: str) -> float:
    """Convert '10mbit', '500kbit', '1gbit' → bits per second."""
    rate_str = rate_str.lower().strip()
    m = re.match(r"([\d.]+)\s*(gbit|mbit|kbit|bit|gbps|mbps|kbps|bps)", rate_str)
    if not m:
        return 0.0
    val = float(m.group(1))
    unit = m.group(2)
    multipliers = {
        "gbit": 1e9, "gbps": 1e9,
        "mbit": 1e6, "mbps": 1e6,
        "kbit": 1e3, "kbps": 1e3,
        "bit": 1, "bps": 1,
    }
    return val * multipliers.get(unit, 1)


def _parse_delay_to_ms(delay_str: str) -> float:
    """Convert '100ms', '0.5s' → milliseconds."""
    delay_str = delay_str.lower().strip()
    m = re.match(r"([\d.]+)\s*(s|ms|us)", delay_str)
    if not m:
        return 0.0
    val = float(m.group(1))
    unit = m.group(2)
    if unit == "s":
        return val * 1000
    elif unit == "us":
        return val / 1000
    return val  # ms


class MetricsCollector:
    """Polls the NetworkEnforcer for tc stats and updates Prometheus gauges."""

    def __init__(self, network_enforcer, intent_manager=None, poll_interval: float = 5.0):
        self._enforcer = network_enforcer
        self._intent_manager = intent_manager
        self._poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(f"Metrics collector started (poll every {self._poll_interval}s)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)

    def _loop(self):
        while self._running:
            try:
                self._collect()
            except Exception as e:
                logger.error(f"Metrics collection error: {e}", exc_info=True)
            time.sleep(self._poll_interval)

    def _collect(self):
        # 1. tc stats
        stats = self._enforcer.collect_tc_stats()
        for device, s in stats.items():
            tc_bytes.labels(device=device).set(s.get("bytes_sent", 0))
            tc_packets.labels(device=device).set(s.get("packets_sent", 0))
            tc_dropped.labels(device=device).set(s.get("dropped", 0))
            tc_overlimits.labels(device=device).set(s.get("overlimits", 0))

        # 2. configured policy values — reset stale device labels first
        active = self._enforcer.get_active_policies()
        policy_active.set(len(active))

        # Track which devices have active policies to clear stale ones
        active_devices = set(active.keys())
        if not hasattr(self, '_prev_devices'):
            self._prev_devices = set()
        stale_devices = self._prev_devices - active_devices
        for dev in stale_devices:
            tc_rate_bps.labels(device=dev).set(0)
            tc_delay_ms.labels(device=dev).set(0)
            tc_priority.labels(device=dev).set(0)
        self._prev_devices = active_devices

        for device, pol in active.items():
            params = pol.get("params", {})
            ptype = pol.get("policy_type", "")

            if "rate" in params:
                tc_rate_bps.labels(device=device).set(
                    _parse_rate_to_bps(params["rate"])
                )
            else:
                tc_rate_bps.labels(device=device).set(0)
            if "delay" in params:
                tc_delay_ms.labels(device=device).set(
                    _parse_delay_to_ms(params["delay"])
                )
            else:
                tc_delay_ms.labels(device=device).set(0)
            if "prio" in params:
                tc_priority.labels(device=device).set(params["prio"])
            else:
                tc_priority.labels(device=device).set(0)

        # 3. intent count
        if self._intent_manager:
            try:
                intents = self._intent_manager.list_intents()
                active_count = sum(
                    1 for i in intents if i.get("status") == "active"
                )
                intent_active.set(active_count)
            except Exception:
                pass


def record_enforcement(policy_type: str, success: bool, duration: float):
    """Called by the dispatch layer after each enforcement operation."""
    status = "success" if success else "failure"
    enforcement_total.labels(policy_type=policy_type, status=status).inc()
    enforcement_latency.labels(policy_type=policy_type).observe(duration)


def record_device_enforcement(policy_type: str, device: str, success: bool):
    """Called by the device enforcer after each MQTT command."""
    status = "success" if success else "failure"
    device_enforcement_total.labels(
        policy_type=policy_type, device=device, status=status
    ).inc()


def record_camera_state(device: str, **kwargs):
    """Update controller-side camera gauges.

    Accepted kwargs:
        resolution  – e.g. 'VGA', 'HD', 'UXGA'
        brightness  – int (-2..+2)
        enabled     – bool
    """
    if 'resolution' in kwargs:
        idx = RESOLUTION_INDEX.get(str(kwargs['resolution']).upper(), -1)
        cam_resolution.labels(device=device).set(idx)
    if 'brightness' in kwargs:
        cam_brightness.labels(device=device).set(kwargs['brightness'])
    if 'enabled' in kwargs:
        cam_enabled.labels(device=device).set(1 if kwargs['enabled'] else 0)


def start_metrics_server(port: int = 8000):
    """Start the Prometheus HTTP exporter on *port*."""
    start_http_server(port, registry=REGISTRY)
    logger.info(f"Prometheus metrics server started on :{port}")
