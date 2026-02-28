#!/usr/bin/env python3
"""
Network Enforcement Module – applies per-device traffic-control policies.

Builds an HTB tree on the chosen interface (typically wlan0) so that each
managed device IP gets its own class with configurable:
  • bandwidth   – HTB rate / ceil
  • latency     – netem delay (optionally with jitter)
  • priority    – HTB prio + strict ordering

Hierarchy
─────────
  root 1: htb  default 99
   ├─ 1:1  root class (link ceiling)
   │   ├─ 1:10  device-class (e.g. esp32-cam-1)  ← filter by dst-IP
   │   │   └─ netem handle 10:  (optional latency)
   │   ├─ 1:20  device-class …
   │   └─ 1:99  default (catch-all)
   └─ filters: u32 match ip dst <device-ip> → flowid 1:<classid>

Every public method is **idempotent** – it tears down the previous config
for that device before re-applying.
"""

import logging
import re
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Docker bridge auto-discovery ─────────────────────────────────────────
def _discover_docker_bridge(network_name: str = "imperium_default") -> str:
    """Return the host-side bridge interface for *network_name*.

    Falls back to 'docker0' if the bridge cannot be determined.
    """
    try:
        import json as _json
        out = subprocess.run(
            ["docker", "network", "inspect", network_name],
            capture_output=True, text=True,
        )
        if out.returncode == 0:
            data = _json.loads(out.stdout)
            net_id = data[0]["Id"][:12]
            candidate = f"br-{net_id}"
            # Verify the interface actually exists
            chk = subprocess.run(
                ["ip", "link", "show", candidate],
                capture_output=True, text=True,
            )
            if chk.returncode == 0:
                return candidate
    except Exception as exc:
        logger.debug(f"Docker bridge discovery failed: {exc}")
    return "docker0"


DOCKER_BRIDGE = _discover_docker_bridge()

# ── Device registry: maps logical name → IP + numeric class-id ──────────
# Class-id must be unique per device; 99 is reserved for the default class.
# Each device specifies its 'iface' – the host interface its traffic crosses.
DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── Physical ESP32 nodes (traffic on wlan0) ──
    "esp32-cam-1":   {"ip": "10.218.189.80",  "classid": 10, "iface": "wlan0"},
    "esp32-mhz19-1": {"ip": "10.218.189.218", "classid": 20, "iface": "wlan0"},
    "esp32-audio-1": {"ip": "10.218.189.218", "classid": 20, "iface": "wlan0"},
}


def _register_docker_sim_nodes() -> None:
    """Populate DEVICE_REGISTRY with Docker sim-node IPs.

    Each sim container gets a unique classid (30 + index) and uses the
    Docker bridge interface.
    """
    for i in range(1, 11):
        container = f"imperium-iot-node-{i}"
        try:
            out = subprocess.run(
                ["docker", "inspect", "-f",
                 "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                 container],
                capture_output=True, text=True,
            )
            ip = out.stdout.strip()
            if out.returncode == 0 and ip:
                DEVICE_REGISTRY[f"node-{i}"] = {
                    "ip": ip,
                    "classid": 30 + i,   # 31 … 40
                    "iface": DOCKER_BRIDGE,
                }
        except Exception:
            pass  # container not running – skip


_register_docker_sim_nodes()

# ── Defaults ─────────────────────────────────────────────────────────────
DEFAULT_LINK_RATE = "50mbit"       # overall ceiling for the interface
DEFAULT_DEV_RATE  = "10mbit"       # per-device default rate
DEFAULT_DEV_CEIL  = "50mbit"       # per-device burst ceiling
DEFAULT_BURST     = "32k"

# Priority mapping: lower number = higher priority in HTB
PRIORITY_MAP = {
    "critical": 0, "high": 1, "medium": 4, "low": 7, "default": 4,
}


class NetworkEnforcer:
    """Idempotent Linux traffic-control enforcer for per-device policies."""

    def __init__(self, interface: str = "wlan0"):
        self.interface = interface  # primary / default interface
        self._lock = threading.Lock()
        # Track what we've applied per device so we can report it
        self._active_policies: Dict[str, Dict] = {}     # device_id → last policy
        self._tc_stats: Dict[str, Dict] = {}             # device_id → latest tc stats

        # All distinct interfaces used by registered devices
        self._interfaces = list({v.get("iface", interface) for v in DEVICE_REGISTRY.values()})
        if interface not in self._interfaces:
            self._interfaces.append(interface)

        # Ensure HTB root on every managed interface
        for iface in self._interfaces:
            self._ensure_root_qdisc(iface)

    # ── public API ───────────────────────────────────────────────────────

    def apply_policy(self, policy: Dict[str, Any]) -> bool:
        """Dispatch a policy dict to the correct handler.  Returns True on success."""
        ptype = policy.get("policy_type", "")
        with self._lock:
            try:
                if ptype in ("bandwidth_limit", "bandwidth"):
                    return self._apply_bandwidth(policy)
                elif ptype in ("latency_control", "latency"):
                    return self._apply_latency(policy)
                elif ptype in ("traffic_shaping", "routing_priority", "priority"):
                    return self._apply_priority(policy)
                else:
                    logger.warning(f"Unknown network policy type: {ptype}")
                    return False
            except Exception as e:
                logger.error(f"Network enforcement failed ({ptype}): {e}", exc_info=True)
                return False

    def clear_device(self, device_id: str) -> bool:
        """Remove all tc rules for *device_id*."""
        info = DEVICE_REGISTRY.get(device_id)
        if not info:
            logger.warning(f"Unknown device: {device_id}")
            return False
        cid = info["classid"]
        iface = info.get("iface", self.interface)
        with self._lock:
            self._del_netem(cid, iface=iface)
            self._del_filter(info["ip"], iface=iface)
            self._del_class(cid, iface=iface)
            self._active_policies.pop(device_id, None)
            logger.info(f"Cleared tc rules for {device_id} on {iface}")
        return True

    def clear_all(self) -> bool:
        """Tear down HTB trees on all managed interfaces."""
        with self._lock:
            for iface in self._interfaces:
                self._tc(["qdisc", "del", "dev", iface, "root"], ok_fail=True)
                logger.info(f"All tc rules cleared on {iface}")
            self._active_policies.clear()
        return True

    def get_status(self) -> Dict[str, Any]:
        """Return current qdisc/class tree and per-device stats."""
        per_iface = {}
        for iface in self._interfaces:
            try:
                per_iface[iface] = {
                    "qdiscs": self._tc_output(["qdisc", "show", "dev", iface]),
                    "classes": self._tc_output(["class", "show", "dev", iface]),
                    "filters": self._tc_output(["filter", "show", "dev", iface]),
                }
            except Exception as e:
                per_iface[iface] = {"error": str(e)}

        return {
            "status": "active",
            "interfaces": per_iface,
            "active_policies": dict(self._active_policies),
        }

    def collect_tc_stats(self) -> Dict[str, Dict]:
        """Parse ``tc -s class show`` on **every** managed interface
        and return per-device byte/pkt counters."""
        from collections import defaultdict

        stats: Dict[str, Dict] = {}

        # Group devices by interface → classid → [device_id, …]
        iface_groups: Dict[str, Dict[int, list]] = defaultdict(lambda: defaultdict(list))
        for dev_id, info in DEVICE_REGISTRY.items():
            iface = info.get("iface", self.interface)
            iface_groups[iface][info["classid"]].append(dev_id)

        for iface, cid_to_devs in iface_groups.items():
            try:
                raw = self._tc_output(["-s", "class", "show", "dev", iface])
            except Exception:
                continue

            current_cid: Optional[int] = None
            for line in raw.splitlines():
                m = re.match(r"class htb 1:(\d+)", line)
                if m:
                    current_cid = int(m.group(1))
                    continue
                if current_cid is not None:
                    m2 = re.match(
                        r"\s+Sent (\d+) bytes (\d+) pkt \(dropped (\d+),\s*overlimits (\d+)",
                        line,
                    )
                    if m2:
                        devs = cid_to_devs.get(current_cid, [])
                        entry = {
                            "bytes_sent": int(m2.group(1)),
                            "packets_sent": int(m2.group(2)),
                            "dropped": int(m2.group(3)),
                            "overlimits": int(m2.group(4)),
                            "classid": current_cid,
                        }
                        for dev in devs:
                            stats[dev] = dict(entry)
                    # rate line
                    m3 = re.match(r"\s+rate (\S+) (\S+)", line)
                    if m3 and current_cid is not None:
                        devs = cid_to_devs.get(current_cid, [])
                        for dev in devs:
                            if dev in stats:
                                stats[dev]["current_rate"] = m3.group(1)
                                stats[dev]["current_pps"] = m3.group(2)
                        current_cid = None  # done with this class block

        self._tc_stats = stats
        return stats

    def get_active_policies(self) -> Dict[str, Dict]:
        return dict(self._active_policies)

    # ── bandwidth ────────────────────────────────────────────────────────

    def _apply_bandwidth(self, policy: Dict) -> bool:
        target = policy.get("target", "")
        params = policy.get("parameters", {})
        info = self._resolve_device(target)
        if not info:
            return False
        cid = info["classid"]
        ip  = info["ip"]
        iface = info.get("iface", self.interface)

        rate = params.get("rate", DEFAULT_DEV_RATE)
        ceil = params.get("ceil", DEFAULT_DEV_CEIL)
        burst = params.get("burst", DEFAULT_BURST)

        self._ensure_root_qdisc(iface)
        self._replace_class(cid, rate, ceil, burst, iface=iface)
        self._ensure_filter(ip, cid, iface=iface)

        self._record(target, "bandwidth_limit", {"rate": rate, "ceil": ceil})
        logger.info(f"✓ Bandwidth for {target} ({ip}@{iface}): rate={rate} ceil={ceil}")
        return True

    # ── latency ──────────────────────────────────────────────────────────

    def _apply_latency(self, policy: Dict) -> bool:
        target = policy.get("target", "")
        params = policy.get("parameters", {})
        info = self._resolve_device(target)
        if not info:
            return False
        cid = info["classid"]
        ip  = info["ip"]
        iface = info.get("iface", self.interface)

        delay = params.get("delay", params.get("netem_delay", "0ms"))
        jitter = params.get("jitter", "0ms")
        loss = params.get("loss", "")

        self._ensure_root_qdisc(iface)
        self._ensure_class(cid, iface=iface)
        self._ensure_filter(ip, cid, iface=iface)

        # Delete any existing netem, then add fresh
        self._del_netem(cid, iface=iface)
        netem_args = [
            "qdisc", "add", "dev", iface,
            "parent", f"1:{cid}", "handle", f"{cid}:",
            "netem", "delay", delay,
        ]
        if jitter and jitter != "0ms":
            netem_args.append(jitter)
        if loss:
            netem_args += ["loss", loss]

        self._tc(netem_args)

        self._record(target, "latency_control", {"delay": delay, "jitter": jitter, "loss": loss})
        logger.info(f"✓ Latency for {target} ({ip}@{iface}): delay={delay} jitter={jitter}")
        return True

    # ── priority ─────────────────────────────────────────────────────────

    def _apply_priority(self, policy: Dict) -> bool:
        target = policy.get("target", "")
        params = policy.get("parameters", {})
        info = self._resolve_device(target)
        if not info:
            return False
        cid = info["classid"]
        ip  = info["ip"]
        iface = info.get("iface", self.interface)

        level = params.get("priority", params.get("level", "medium"))
        if isinstance(level, str):
            prio = PRIORITY_MAP.get(level.lower(), 4)
        else:
            prio = int(level)

        # Use explicit rate/ceil from policy if provided, otherwise keep existing
        # (avoids second policy overwriting bandwidth set by a companion policy)
        existing_params = self._active_policies.get(target, {}).get("params", {})
        rate = params.get("rate", existing_params.get("rate", DEFAULT_DEV_RATE))
        ceil = params.get("ceil", existing_params.get("ceil", DEFAULT_DEV_CEIL))

        self._ensure_root_qdisc(iface)
        self._replace_class(cid, rate, ceil, DEFAULT_BURST, prio=prio, iface=iface)
        self._ensure_filter(ip, cid, iface=iface)

        self._record(target, "priority", {"priority": level, "prio": prio, "rate": rate, "ceil": ceil})
        logger.info(f"✓ Priority for {target} ({ip}@{iface}): {level} (prio={prio})")
        return True

    # ── tc helper methods ────────────────────────────────────────────────

    def _ensure_root_qdisc(self, iface: Optional[str] = None):
        """Create root HTB qdisc + umbrella class if missing on *iface*."""
        iface = iface or self.interface
        out = self._tc_output(["qdisc", "show", "dev", iface])
        if "htb 1:" in out:
            # Root exists — just make sure per-device classes are present
            self._ensure_device_classes(iface)
            return

        # Use 'replace' to overwrite whatever root qdisc exists (e.g. fq_codel)
        self._tc([
            "qdisc", "replace", "dev", iface,
            "root", "handle", "1:", "htb", "default", "99",
        ], ok_fail=True)

        self._tc([
            "class", "add", "dev", iface,
            "parent", "1:", "classid", "1:1", "htb",
            "rate", DEFAULT_LINK_RATE, "ceil", DEFAULT_LINK_RATE,
        ], ok_fail=True)

        self._tc([
            "class", "add", "dev", iface,
            "parent", "1:1", "classid", "1:99", "htb",
            "rate", DEFAULT_DEV_RATE, "ceil", DEFAULT_LINK_RATE,
        ], ok_fail=True)
        logger.info(f"HTB root tree created on {iface}")

        # Now create per-device classes so tc stats are always available
        self._ensure_device_classes(iface)

    def _ensure_device_classes(self, iface: Optional[str] = None):
        """Create an HTB class + u32 filter for every device on *iface*.

        This ensures ``collect_tc_stats()`` always has per-device counters,
        even before any intent has been submitted.  Idempotent — skips
        classes that already exist.
        """
        iface = iface or self.interface
        seen_cids: set = set()
        for dev_id, info in DEVICE_REGISTRY.items():
            if info.get("iface", self.interface) != iface:
                continue  # belongs to a different interface
            cid = info["classid"]
            if cid in seen_cids:
                continue  # esp32-audio-1 shares classid with esp32-mhz19-1
            seen_cids.add(cid)
            self._ensure_class(cid, iface=iface)
            self._ensure_filter(info["ip"], cid, iface=iface)
        if seen_cids:
            logger.info(
                f"Per-device HTB classes ensured for classids {sorted(seen_cids)} "
                f"on {iface}"
            )

    def _replace_class(self, cid: int, rate: str, ceil: str, burst: str,
                        prio: int = 4, iface: Optional[str] = None):
        """Add-or-replace an HTB class under 1:1."""
        iface = iface or self.interface
        rc = self._tc([
            "class", "change", "dev", iface,
            "parent", "1:1", "classid", f"1:{cid}", "htb",
            "rate", rate, "ceil", ceil, "burst", burst, "prio", str(prio),
        ], ok_fail=True)
        if rc != 0:
            self._tc([
                "class", "add", "dev", iface,
                "parent", "1:1", "classid", f"1:{cid}", "htb",
                "rate", rate, "ceil", ceil, "burst", burst, "prio", str(prio),
            ])

    def _ensure_class(self, cid: int, iface: Optional[str] = None):
        """Make sure a class exists (with defaults) – idempotent."""
        iface = iface or self.interface
        out = self._tc_output(["class", "show", "dev", iface])
        if f"1:{cid} " in out:
            return
        self._replace_class(cid, DEFAULT_DEV_RATE, DEFAULT_DEV_CEIL, DEFAULT_BURST, iface=iface)

    def _del_class(self, cid: int, iface: Optional[str] = None):
        iface = iface or self.interface
        self._tc([
            "class", "del", "dev", iface,
            "parent", "1:1", "classid", f"1:{cid}",
        ], ok_fail=True)

    @staticmethod
    def _ip_to_hex(ip: str) -> str:
        """Convert dotted-quad IP to lowercase hex (e.g. '10.218.189.80' → '0adabd50')."""
        import socket, struct
        return format(struct.unpack('!I', socket.inet_aton(ip))[0], '08x')

    def _ensure_filter(self, ip: str, cid: int, iface: Optional[str] = None):
        """Add a u32 filter for *ip* → classid 1:<cid> if not present."""
        iface = iface or self.interface
        out = self._tc_output(["filter", "show", "dev", iface])
        # tc filter show prints IPs as hex (e.g. 0adabd50), check both forms
        ip_hex = self._ip_to_hex(ip)
        if ip_hex in out or ip in out:
            return
        self._tc([
            "filter", "add", "dev", iface,
            "protocol", "ip", "parent", "1:0", "prio", "1",
            "u32", "match", "ip", "dst", f"{ip}/32",
            "flowid", f"1:{cid}",
        ])
        logger.debug(f"Filter added: {ip} → 1:{cid} on {iface}")

    def _del_filter(self, ip: str, iface: Optional[str] = None):
        """Remove filter for *ip* by flushing and re-adding others."""
        iface = iface or self.interface
        out = self._tc_output(["filter", "show", "dev", iface])
        ip_hex = self._ip_to_hex(ip)
        if ip_hex not in out and ip not in out:
            return
        self._tc(["filter", "del", "dev", iface, "parent", "1:0"], ok_fail=True)
        for dev_id, dev_info in DEVICE_REGISTRY.items():
            if dev_info["ip"] == ip:
                continue
            if dev_info.get("iface", self.interface) != iface:
                continue  # different interface — skip
            if dev_id in self._active_policies:
                self._ensure_filter(dev_info["ip"], dev_info["classid"], iface=iface)

    def _del_netem(self, cid: int, iface: Optional[str] = None):
        """Remove netem qdisc from class (ignore errors if absent)."""
        iface = iface or self.interface
        self._tc([
            "qdisc", "del", "dev", iface,
            "parent", f"1:{cid}", "handle", f"{cid}:",
        ], ok_fail=True)

    def _tc(self, args: List[str], ok_fail: bool = False) -> int:
        """Run a tc command.  Returns exit code."""
        cmd = ["sudo", "tc"] + args
        logger.debug(f"tc: {' '.join(cmd)}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 and not ok_fail:
            logger.error(f"tc failed ({r.returncode}): {r.stderr.strip()}")
            raise RuntimeError(f"tc failed: {r.stderr.strip()}")
        return r.returncode

    def _tc_output(self, args: List[str]) -> str:
        cmd = ["sudo", "tc"] + args
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.stdout

    # ── bookkeeping ──────────────────────────────────────────────────────

    def _resolve_device(self, target: str) -> Optional[Dict]:
        info = DEVICE_REGISTRY.get(target)
        if not info:
            logger.warning(f"Device '{target}' not in DEVICE_REGISTRY – known: {list(DEVICE_REGISTRY.keys())}")
            return None
        # Ensure 'iface' is always present (defaults to primary)
        if "iface" not in info:
            info["iface"] = self.interface
        return info

    def _record(self, device_id: str, policy_type: str, params: Dict):
        """Record applied policy, merging params with any existing record for this device."""
        existing = self._active_policies.get(device_id, {})
        merged_params = existing.get("params", {})
        merged_params.update(params)
        self._active_policies[device_id] = {
            "policy_type": policy_type,
            "params": merged_params,
            "applied_at": time.time(),
        }
