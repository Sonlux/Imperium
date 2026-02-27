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

# ── Device registry: maps logical name → IP + numeric class-id ──────────
# Class-id must be unique per device; 99 is reserved for the default class.
DEVICE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "esp32-cam-1":   {"ip": "10.218.189.80",  "classid": 10},
    "esp32-mhz19-1": {"ip": "10.218.189.218", "classid": 20},
    "esp32-audio-1": {"ip": "10.218.189.218", "classid": 20},  # same physical chip
}

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
        self.interface = interface
        self._lock = threading.Lock()
        # Track what we've applied per device so we can report it
        self._active_policies: Dict[str, Dict] = {}     # device_id → last policy
        self._tc_stats: Dict[str, Dict] = {}             # device_id → latest tc stats
        self._ensure_root_qdisc()

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
        with self._lock:
            self._del_netem(cid)
            self._del_filter(info["ip"])
            self._del_class(cid)
            self._active_policies.pop(device_id, None)
            logger.info(f"Cleared tc rules for {device_id}")
        return True

    def clear_all(self) -> bool:
        """Tear down the entire HTB tree."""
        with self._lock:
            self._tc(["qdisc", "del", "dev", self.interface, "root"], ok_fail=True)
            self._active_policies.clear()
            logger.info(f"All tc rules cleared on {self.interface}")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Return current qdisc/class tree and per-device stats."""
        try:
            qdiscs = self._tc_output(["qdisc", "show", "dev", self.interface])
            classes = self._tc_output(["class", "show", "dev", self.interface])
            filters = self._tc_output(["filter", "show", "dev", self.interface])
        except Exception as e:
            return {"status": "error", "error": str(e)}

        return {
            "status": "active",
            "interface": self.interface,
            "qdiscs": qdiscs,
            "classes": classes,
            "filters": filters,
            "active_policies": dict(self._active_policies),
        }

    def collect_tc_stats(self) -> Dict[str, Dict]:
        """Parse ``tc -s class show`` and return per-device byte/pkt counters."""
        try:
            raw = self._tc_output(["-s", "class", "show", "dev", self.interface])
        except Exception:
            return {}

        stats: Dict[str, Dict] = {}
        # Build reverse map classid → device_id
        cid_to_dev = {v["classid"]: k for k, v in DEVICE_REGISTRY.items()}

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
                    dev = cid_to_dev.get(current_cid)
                    if dev:
                        stats[dev] = {
                            "bytes_sent": int(m2.group(1)),
                            "packets_sent": int(m2.group(2)),
                            "dropped": int(m2.group(3)),
                            "overlimits": int(m2.group(4)),
                            "classid": current_cid,
                        }
                # rate line
                m3 = re.match(r"\s+rate (\S+) (\S+)", line)
                if m3 and current_cid is not None:
                    dev = cid_to_dev.get(current_cid)
                    if dev and dev in stats:
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

        rate = params.get("rate", DEFAULT_DEV_RATE)
        ceil = params.get("ceil", DEFAULT_DEV_CEIL)
        burst = params.get("burst", DEFAULT_BURST)

        self._ensure_root_qdisc()
        self._replace_class(cid, rate, ceil, burst)
        self._ensure_filter(ip, cid)

        self._record(target, "bandwidth_limit", {"rate": rate, "ceil": ceil})
        logger.info(f"✓ Bandwidth for {target} ({ip}): rate={rate} ceil={ceil}")
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

        delay = params.get("delay", params.get("netem_delay", "0ms"))
        jitter = params.get("jitter", "0ms")
        loss = params.get("loss", "")

        self._ensure_root_qdisc()
        self._ensure_class(cid)
        self._ensure_filter(ip, cid)

        # Delete any existing netem, then add fresh
        self._del_netem(cid)
        netem_args = [
            "qdisc", "add", "dev", self.interface,
            "parent", f"1:{cid}", "handle", f"{cid}:",
            "netem", "delay", delay,
        ]
        if jitter and jitter != "0ms":
            netem_args.append(jitter)
        if loss:
            netem_args += ["loss", loss]

        self._tc(netem_args)

        self._record(target, "latency_control", {"delay": delay, "jitter": jitter, "loss": loss})
        logger.info(f"✓ Latency for {target} ({ip}): delay={delay} jitter={jitter}")
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

        self._ensure_root_qdisc()
        self._replace_class(cid, rate, ceil, DEFAULT_BURST, prio=prio)
        self._ensure_filter(ip, cid)

        self._record(target, "priority", {"priority": level, "prio": prio, "rate": rate, "ceil": ceil})
        logger.info(f"✓ Priority for {target} ({ip}): {level} (prio={prio})")
        return True

    # ── tc helper methods ────────────────────────────────────────────────

    def _ensure_root_qdisc(self):
        """Create root HTB qdisc + umbrella class if missing."""
        out = self._tc_output(["qdisc", "show", "dev", self.interface])
        if "htb 1:" in out:
            return

        # Use 'replace' to overwrite whatever root qdisc exists (e.g. fq_codel)
        self._tc([
            "qdisc", "replace", "dev", self.interface,
            "root", "handle", "1:", "htb", "default", "99",
        ], ok_fail=True)

        self._tc([
            "class", "add", "dev", self.interface,
            "parent", "1:", "classid", "1:1", "htb",
            "rate", DEFAULT_LINK_RATE, "ceil", DEFAULT_LINK_RATE,
        ], ok_fail=True)

        self._tc([
            "class", "add", "dev", self.interface,
            "parent", "1:1", "classid", "1:99", "htb",
            "rate", DEFAULT_DEV_RATE, "ceil", DEFAULT_LINK_RATE,
        ], ok_fail=True)
        logger.info(f"HTB root tree created on {self.interface}")

    def _replace_class(self, cid: int, rate: str, ceil: str, burst: str, prio: int = 4):
        """Add-or-replace an HTB class under 1:1."""
        rc = self._tc([
            "class", "change", "dev", self.interface,
            "parent", "1:1", "classid", f"1:{cid}", "htb",
            "rate", rate, "ceil", ceil, "burst", burst, "prio", str(prio),
        ], ok_fail=True)
        if rc != 0:
            self._tc([
                "class", "add", "dev", self.interface,
                "parent", "1:1", "classid", f"1:{cid}", "htb",
                "rate", rate, "ceil", ceil, "burst", burst, "prio", str(prio),
            ])

    def _ensure_class(self, cid: int):
        """Make sure a class exists (with defaults) – idempotent."""
        out = self._tc_output(["class", "show", "dev", self.interface])
        if f"1:{cid} " in out:
            return
        self._replace_class(cid, DEFAULT_DEV_RATE, DEFAULT_DEV_CEIL, DEFAULT_BURST)

    def _del_class(self, cid: int):
        self._tc([
            "class", "del", "dev", self.interface,
            "parent", "1:1", "classid", f"1:{cid}",
        ], ok_fail=True)

    @staticmethod
    def _ip_to_hex(ip: str) -> str:
        """Convert dotted-quad IP to lowercase hex (e.g. '10.218.189.80' → '0adabd50')."""
        import socket, struct
        return format(struct.unpack('!I', socket.inet_aton(ip))[0], '08x')

    def _ensure_filter(self, ip: str, cid: int):
        """Add a u32 filter for *ip* → classid 1:<cid> if not present."""
        out = self._tc_output(["filter", "show", "dev", self.interface])
        # tc filter show prints IPs as hex (e.g. 0adabd50), check both forms
        ip_hex = self._ip_to_hex(ip)
        if ip_hex in out or ip in out:
            return
        self._tc([
            "filter", "add", "dev", self.interface,
            "protocol", "ip", "parent", "1:0", "prio", "1",
            "u32", "match", "ip", "dst", f"{ip}/32",
            "flowid", f"1:{cid}",
        ])
        logger.debug(f"Filter added: {ip} → 1:{cid}")

    def _del_filter(self, ip: str):
        """Remove filter for *ip* by flushing and re-adding others."""
        out = self._tc_output(["filter", "show", "dev", self.interface])
        ip_hex = self._ip_to_hex(ip)
        if ip_hex not in out and ip not in out:
            return
        self._tc(["filter", "del", "dev", self.interface, "parent", "1:0"], ok_fail=True)
        for dev_id, dev_info in DEVICE_REGISTRY.items():
            if dev_info["ip"] == ip:
                continue
            if dev_id in self._active_policies:
                self._ensure_filter(dev_info["ip"], dev_info["classid"])

    def _del_netem(self, cid: int):
        """Remove netem qdisc from class (ignore errors if absent)."""
        self._tc([
            "qdisc", "del", "dev", self.interface,
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
