import os
import sys
import time
import ctypes
import threading
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from backend.ml.predict import is_broadcast_or_multicast_address
from backend.app.utils.logger import logger

try:
    from scapy.all import AsyncSniffer, conf, get_working_ifaces, IP, IPv6, TCP, UDP, ICMP
    SCAPY_AVAILABLE = True
except Exception as e:
    SCAPY_AVAILABLE = False
    SCAPY_IMPORT_ERROR = str(e)

INTERFACE_VISIBILITY_NOTICE = (
    "Passive Capture Visibility Scope: Capturing on a local Wi-Fi or Ethernet interface observes traffic "
    "sent to/from this host plus broadcast/multicast frames on the local segment. Unicast traffic between "
    "other separate devices on a switched network or encrypted Wi-Fi AP is not visible without switch port "
    "mirroring (SPAN) or an inline network tap."
)

WELL_KNOWN_SERVICES: Dict[int, str] = {
    20: "ftp_data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "domain_u",
    67: "other",
    68: "other",
    69: "tftp_u",
    70: "gopher",
    79: "finger",
    80: "http",
    88: "other",
    109: "pop_2",
    110: "pop_3",
    111: "sunrpc",
    113: "auth",
    119: "nntp",
    123: "ntp_u",
    135: "other",
    137: "netbios_ns",
    138: "netbios_dgm",
    139: "netbios_ssn",
    143: "imap4",
    161: "other",
    162: "other",
    179: "bgp",
    194: "IRC",
    389: "ldap",
    443: "http",       # Mapped to 'http' / 'http_443' compatible baseline
    445: "netbios_ssn",
    465: "smtp",
    512: "exec",
    513: "login",
    514: "shell",
    515: "printer",
    520: "efs",
    540: "uucp",
    543: "klogin",
    544: "kshell",
    587: "smtp",
    636: "ldap",
    873: "other",
    993: "imap4",
    995: "pop_3",
    1433: "sql_net",
    1521: "sql_net",
    1900: "other",
    2049: "other",
    3000: "http",
    3306: "sql_net",
    3389: "other",
    5173: "http",
    5353: "domain_u",
    5355: "domain_u",
    5432: "sql_net",
    6000: "X11",
    6667: "IRC",
    8000: "http",
    8001: "http_8001",
    8008: "http",
    8009: "http",
    8080: "http",
    8443: "http_443",
}


def check_is_admin() -> bool:
    """Check if the current process has Administrator (Windows) or root (POSIX) privileges."""
    try:
        if os.name == "nt" and hasattr(ctypes, "windll"):
            return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)
        return os.geteuid() == 0
    except Exception:
        return False


def check_npcap_installed() -> bool:
    """Check if Npcap / WinPcap is installed and available to Scapy."""
    if os.name == "nt":
        npcap_paths = [
            r"C:\Windows\System32\Npcap",
            r"C:\Program Files\Npcap",
            r"C:\Windows\SysWOW64\Npcap",
        ]
        if any(os.path.exists(p) for p in npcap_paths):
            return True
    if SCAPY_AVAILABLE:
        return bool(getattr(conf, "use_pcap", False))
    return False


def list_network_interfaces() -> List[Dict[str, Any]]:
    """
    Enumerate working network interfaces via Scapy/Npcap, prioritizing physical
    Windows Wi-Fi and Ethernet adapters with active IPv4 addresses.
    """
    if not SCAPY_AVAILABLE:
        return []

    interfaces: List[Dict[str, Any]] = []
    try:
        working_ifaces = get_working_ifaces()
    except Exception:
        working_ifaces = []

    for iface in working_ifaces:
        name = str(getattr(iface, "name", "") or "")
        description = str(getattr(iface, "description", "") or name)
        ip = str(getattr(iface, "ip", "") or "")
        mac = str(getattr(iface, "mac", "") or "")
        network_name = str(getattr(iface, "network_name", "") or name)

        combined_lower = f"{name} {description}".lower()

        # Skip unaddressed WAN Miniport pseudodevices that cannot capture standard IP frames cleanly
        if "wan miniport" in combined_lower and not ip:
            continue

        if "wi-fi" in combined_lower or "wireless" in combined_lower or "wlan" in combined_lower or "802.11" in combined_lower:
            if "direct" in combined_lower or "virtual" in combined_lower:
                iface_type = "Virtual Wi-Fi"
            else:
                iface_type = "Wi-Fi"
        elif "loopback" in combined_lower or ip == "127.0.0.1":
            iface_type = "Loopback"
        elif "vmware" in combined_lower or "virtualbox" in combined_lower or "vethernet" in combined_lower or "tap-" in combined_lower or "tun" in combined_lower or "hyper-v" in combined_lower:
            iface_type = "Virtual"
        elif "ethernet" in combined_lower or "realtek" in combined_lower or "intel" in combined_lower or "gbefamily" in combined_lower:
            iface_type = "Ethernet"
        else:
            iface_type = "Adapter"

        has_valid_lan_ip = bool(ip and ip != "127.0.0.1" and not ip.startswith("169.254.") and not ip.startswith("0."))

        # Priority score for auto-selecting the primary interface
        priority = 0
        if iface_type == "Wi-Fi" and has_valid_lan_ip:
            priority = 100
        elif iface_type == "Ethernet" and has_valid_lan_ip:
            priority = 95
        elif has_valid_lan_ip and iface_type not in ("Virtual", "Loopback"):
            priority = 80
        elif has_valid_lan_ip:
            priority = 50
        elif iface_type == "Loopback":
            priority = 30
        elif ip:
            priority = 20
        else:
            priority = 5

        interfaces.append({
            "name": name,
            "description": description,
            "ip": ip or "No IPv4",
            "mac": mac,
            "network_name": network_name,
            "type": iface_type,
            "is_active_lan": has_valid_lan_ip,
            "priority": priority,
        })

    interfaces.sort(key=lambda x: x["priority"], reverse=True)
    return interfaces


class BaseTrafficAdapter(ABC):
    @abstractmethod
    def capture_next_packet(self) -> Optional[dict]:
        """Capture or retrieve the next aggregated traffic flow dictionary."""
        pass


class FlowState:
    """Tracks bidirectional packet statistics for a single 5-tuple network flow."""
    def __init__(
        self,
        flow_key: Tuple[str, str, int, int, str],
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        service: str,
        timestamp: float,
    ):
        self.flow_key = flow_key
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.protocol = protocol  # 'tcp', 'udp', 'icmp'
        self.service = service

        self.first_seen: float = timestamp
        self.last_seen: float = timestamp
        self.last_emitted_at: float = 0.0
        self.emitted_packets: int = 0

        self.src_bytes: int = 0
        self.dst_bytes: int = 0
        self.fwd_packets: int = 0
        self.rev_packets: int = 0
        self.total_packets: int = 0

        # TCP state tracking for NSL-KDD flag derivation
        self.fwd_syn: bool = False
        self.fwd_ack: bool = False
        self.fwd_fin: bool = False
        self.fwd_rst: bool = False
        self.fwd_psh: bool = False

        self.rev_syn: bool = False
        self.rev_ack: bool = False
        self.rev_fin: bool = False
        self.rev_rst: bool = False
        self.rev_psh: bool = False

    def update(self, pkt_src: str, pkt_len: int, tcp_flags: str, timestamp: float):
        self.last_seen = timestamp
        self.total_packets += 1
        is_forward = (pkt_src == self.src_ip)

        if is_forward:
            self.fwd_packets += 1
            self.src_bytes += pkt_len
            if "S" in tcp_flags and "A" not in tcp_flags:
                self.fwd_syn = True
            if "A" in tcp_flags:
                self.fwd_ack = True
            if "F" in tcp_flags:
                self.fwd_fin = True
            if "R" in tcp_flags:
                self.fwd_rst = True
            if "P" in tcp_flags:
                self.fwd_psh = True
        else:
            self.rev_packets += 1
            self.dst_bytes += pkt_len
            if "S" in tcp_flags:
                self.rev_syn = True
            if "A" in tcp_flags:
                self.rev_ack = True
            if "F" in tcp_flags:
                self.rev_fin = True
            if "R" in tcp_flags:
                self.rev_rst = True
            if "P" in tcp_flags:
                self.rev_psh = True

    def derive_nsl_kdd_flag(self) -> str:
        """Map observed flow state to one of the 11 NSL-KDD flag classes."""
        if self.protocol in ("udp", "icmp"):
            return "SF"

        # TCP flag state derivation
        if self.rev_rst and self.fwd_syn and not self.rev_syn and self.dst_bytes <= 60:
            return "REJ"  # Connection attempt rejected via RST
        if self.fwd_rst:
            if self.fwd_syn and not self.rev_syn and not self.rev_ack:
                return "RSTOS0"
            return "RSTO"
        if self.rev_rst:
            return "RSTR"
        if self.fwd_syn and not self.rev_syn and not self.rev_ack and self.rev_packets == 0:
            if self.fwd_fin:
                return "SH"
            return "S0"  # SYN sent, no reply seen

        # If data or ACKs have been exchanged normally (including already-established connections)
        if (self.fwd_ack or self.rev_ack) or (self.src_bytes > 0 and self.dst_bytes > 0):
            return "SF"

        if self.fwd_syn and self.rev_syn:
            return "S1"

        return "SF"

    def derive_logged_in(self, flag: str) -> int:
        """Infer NSL-KDD logged_in attribute (1 if established application session, 0 otherwise)."""
        if self.protocol != "tcp" or flag != "SF":
            return 0
        if (self.fwd_psh or self.rev_psh or (self.src_bytes > 60 and self.dst_bytes > 60)):
            return 1
        if self.service in ("http", "http_443", "ssh", "ftp", "smtp", "imap4", "pop_3", "telnet", "login", "shell"):
            return 1
        return 0


class FlowAggregator:
    """
    Aggregates raw captured packets into bidirectional 5-tuple network flows and
    computes the 20 NSL-KDD features using a 2-second time window and 100-flow host window.
    """
    def __init__(self, flow_timeout: float = 30.0, min_emit_interval: float = 0.6):
        self.flow_timeout = flow_timeout
        self.min_emit_interval = min_emit_interval
        self.active_flows: Dict[Tuple[str, str, int, int, str], FlowState] = {}
        # History of emitted flow summaries: (timestamp, src_ip, dst_ip, src_port, dst_port, protocol, service, flag)
        self.recent_connections: deque = deque(maxlen=250)
        self._lock = threading.Lock()

    @staticmethod
    def _infer_service(protocol: str, src_port: int, dst_port: int, icmp_type: int = 8) -> str:
        if protocol == "icmp":
            if icmp_type == 8:
                return "eco_i"
            elif icmp_type == 0:
                return "ecr_i"
            return "urp_i"

        # UDP/443 is QUIC (HTTP/3 over UDP), not TCP HTTP. In the NSL-KDD encoder,
        # map UDP/443 to 'other' so it is not conflated with TCP HTTP/1.x.
        if protocol == "udp" and (dst_port == 443 or src_port == 443):
            return "other"

        if dst_port in WELL_KNOWN_SERVICES:
            svc = WELL_KNOWN_SERVICES[dst_port]
        elif src_port in WELL_KNOWN_SERVICES:
            svc = WELL_KNOWN_SERVICES[src_port]
        elif dst_port < 1024:
            svc = "other"
        else:
            svc = "private"

        # Differentiate TCP vs UDP DNS
        if svc == "domain_u" and protocol == "tcp":
            return "domain"
        return svc

    @classmethod
    def _orient_endpoints(
        cls, src_ip: str, dst_ip: str, src_port: int, dst_port: int, protocol: str, tcp_flags: str
    ) -> Tuple[str, str, int, int]:
        """
        Orient flow endpoints as (client_ip, server_ip, client_port, server_port) so that
        mid-stream captured packets still map client->server accurately, without inverting
        unidirectional UDP broadcast/discovery packets.
        """
        if is_broadcast_or_multicast_address(dst_ip):
            return src_ip, dst_ip, src_port, dst_port

        if protocol == "udp":
            # For connectionless UDP, only flip if the packet is a reply from a standard
            # query-response service port (DNS 53, NTP 123, QUIC 443) to an ephemeral port
            udp_server_ports = {53, 67, 123, 161, 389, 443}
            if src_port in udp_server_ports and dst_port >= 1024 and dst_port not in udp_server_ports:
                return dst_ip, src_ip, dst_port, src_port
            return src_ip, dst_ip, src_port, dst_port

        if protocol == "icmp":
            return src_ip, dst_ip, src_port, dst_port

        if protocol == "tcp" and "S" in tcp_flags and "A" not in tcp_flags:
            return src_ip, dst_ip, src_port, dst_port

        # If src_port is a known service port and dst_port is an ephemeral port, flip so dst is server
        src_is_known = src_port in WELL_KNOWN_SERVICES or (0 < src_port < 1024)
        dst_is_known = dst_port in WELL_KNOWN_SERVICES or (0 < dst_port < 1024)

        if src_is_known and not dst_is_known:
            return dst_ip, src_ip, dst_port, src_port
        if dst_is_known and not src_is_known:
            return src_ip, dst_ip, src_port, dst_port

        # If neither is in WELL_KNOWN_SERVICES, prefer lower port as server port if < 10000
        if src_port < dst_port and src_port < 10000 and dst_port >= 10000:
            return dst_ip, src_ip, dst_port, src_port

        return src_ip, dst_ip, src_port, dst_port

    def ingest_packet(self, pkt) -> Optional[Dict[str, Any]]:
        """
        Process a Scapy packet, update flow state, and return a ready flow dictionary
        when the flow reaches emission criteria.
        """
        now = time.time()
        pkt_info = self._extract_packet_metadata(pkt, now)
        if not pkt_info:
            return None

        return self.ingest_parsed_packet(**pkt_info)

    @staticmethod
    def _extract_packet_metadata(pkt, timestamp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        now = timestamp or time.time()
        if IP in pkt:
            ip_layer = pkt[IP]
            src_ip = str(ip_layer.src)
            dst_ip = str(ip_layer.dst)
        elif IPv6 in pkt:
            ip_layer = pkt[IPv6]
            src_ip = str(ip_layer.src)
            dst_ip = str(ip_layer.dst)
        else:
            return None

        pkt_len = len(pkt)
        src_port = 0
        dst_port = 0
        tcp_flags = ""
        icmp_type = 8

        if TCP in pkt:
            protocol = "tcp"
            tcp_layer = pkt[TCP]
            src_port = int(tcp_layer.sport)
            dst_port = int(tcp_layer.dport)
            tcp_flags = str(tcp_layer.flags)
        elif UDP in pkt:
            protocol = "udp"
            udp_layer = pkt[UDP]
            src_port = int(udp_layer.sport)
            dst_port = int(udp_layer.dport)
        elif ICMP in pkt:
            protocol = "icmp"
            icmp_layer = pkt[ICMP]
            icmp_type = int(getattr(icmp_layer, "type", 8))
        else:
            return None

        return {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
            "pkt_len": pkt_len,
            "tcp_flags": tcp_flags,
            "icmp_type": icmp_type,
            "timestamp": now,
        }

    def ingest_parsed_packet(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: str,
        pkt_len: int,
        tcp_flags: str = "",
        icmp_type: int = 8,
        timestamp: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        now = timestamp or time.time()

        with self._lock:
            # Expire stale flows
            stale_keys = [
                k for k, fl in self.active_flows.items()
                if (now - fl.last_seen) > self.flow_timeout
            ]
            for k in stale_keys:
                del self.active_flows[k]

            # Check if flow already exists in either direction
            fwd_key = (src_ip, dst_ip, src_port, dst_port, protocol)
            rev_key = (dst_ip, src_ip, dst_port, src_port, protocol)

            if fwd_key in self.active_flows:
                flow = self.active_flows[fwd_key]
            elif rev_key in self.active_flows:
                flow = self.active_flows[rev_key]
            else:
                c_ip, s_ip, c_port, s_port = self._orient_endpoints(
                    src_ip, dst_ip, src_port, dst_port, protocol, tcp_flags
                )
                canon_key = (c_ip, s_ip, c_port, s_port, protocol)
                service = self._infer_service(protocol, c_port, s_port, icmp_type)
                flow = FlowState(
                    flow_key=canon_key,
                    src_ip=c_ip,
                    dst_ip=s_ip,
                    src_port=c_port,
                    dst_port=s_port,
                    protocol=protocol,
                    service=service,
                    timestamp=now,
                )
                self.active_flows[canon_key] = flow

            flow.update(pkt_src=src_ip, pkt_len=pkt_len, tcp_flags=tcp_flags, timestamp=now)

            # Determine if flow is ready to emit a snapshot
            time_since_first = now - flow.first_seen
            time_since_emit = now - flow.last_emitted_at
            new_packets = flow.total_packets - flow.emitted_packets

            is_closing = ("F" in tcp_flags or "R" in tcp_flags)
            has_bidirectional = (flow.fwd_packets > 0 and flow.rev_packets > 0)
            already_emitted_once = (flow.last_emitted_at > 0.0)
            effective_interval = max(self.min_emit_interval, 4.0) if already_emitted_once else self.min_emit_interval

            should_emit = False
            if is_closing and new_packets >= 1:
                should_emit = True
            elif has_bidirectional and new_packets >= 2 and time_since_emit >= effective_interval:
                should_emit = True
            elif new_packets >= 5 and has_bidirectional and time_since_emit >= effective_interval:
                should_emit = True
            elif time_since_first >= 0.8 and time_since_emit >= max(0.8, effective_interval) and new_packets >= 1:
                should_emit = True

            if should_emit:
                return self._build_flow_record(flow, now)
            return None

    def flush_ready_flows(self, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Flush flows that have accumulated packets and waited >= 0.7s (e.g. UDP/ICMP or unanswered SYNs)."""
        now = now or time.time()
        ready_records: List[Dict[str, Any]] = []
        with self._lock:
            for flow in list(self.active_flows.values()):
                new_packets = flow.total_packets - flow.emitted_packets
                age_since_first = now - flow.first_seen
                age_since_emit = now - flow.last_emitted_at
                min_wait = 4.0 if flow.last_emitted_at > 0.0 else 0.65
                if new_packets >= 1 and age_since_first >= 0.65 and age_since_emit >= min_wait:
                    ready_records.append(self._build_flow_record(flow, now))
        return ready_records

    def _build_flow_record(self, flow: FlowState, now: float) -> Dict[str, Any]:
        """Compute all 20 NSL-KDD features for the given flow and return the structured record."""
        flow.last_emitted_at = now
        flow.emitted_packets = flow.total_packets

        duration = min(15.0, max(0.0, round(flow.last_seen - flow.first_seen, 4)))
        flag = flow.derive_nsl_kdd_flag()
        logged_in = flow.derive_logged_in(flag)
        is_bcast = is_broadcast_or_multicast_address(flow.dst_ip)

        # Record this unique connection (5-tuple) in sliding history window without duplicating ongoing flows
        conn_entry = {
            "flow_key": flow.flow_key,
            "timestamp": now,
            "src_ip": flow.src_ip,
            "dst_ip": flow.dst_ip,
            "src_port": flow.src_port,
            "dst_port": flow.dst_port,
            "protocol": flow.protocol,
            "service": flow.service,
            "flag": flag,
        }
        existing_idx = next(
            (idx for idx, c in enumerate(self.recent_connections) if c.get("flow_key") == flow.flow_key),
            None,
        )
        if existing_idx is not None:
            self.recent_connections[existing_idx] = conn_entry
        else:
            self.recent_connections.append(conn_entry)

        # 1. Time-based traffic features (last 2.0 seconds window)
        two_sec_ago = now - 2.0
        recent_2s = [c for c in self.recent_connections if c["timestamp"] >= two_sec_ago]

        same_dst_2s = [c for c in recent_2s if c["dst_ip"] == flow.dst_ip]
        same_srv_2s = [c for c in recent_2s if c["service"] == flow.service]

        count = max(1, len(same_dst_2s))
        srv_count = max(1, len(same_srv_2s))

        serror_flags = {"S0", "S1", "S2", "S3"}
        rerror_flags = {"REJ", "RSTO", "RSTR", "RSTOS0"}

        serror_count_2s = sum(1 for c in same_dst_2s if c["flag"] in serror_flags)
        srv_serror_count_2s = sum(1 for c in same_srv_2s if c["flag"] in serror_flags)
        same_srv_in_dst_2s = sum(1 for c in same_dst_2s if c["service"] == flow.service)
        diff_srv_in_dst_2s = count - same_srv_in_dst_2s

        serror_rate = round(serror_count_2s / count, 4)
        srv_serror_rate = round(srv_serror_count_2s / srv_count, 4)
        same_srv_rate = round(same_srv_in_dst_2s / count, 4)
        diff_srv_rate = round(diff_srv_in_dst_2s / count, 4)

        # 2. Host-based traffic features (last 100 connections window)
        last_100 = list(self.recent_connections)[-100:]
        same_dst_host = [c for c in last_100 if c["dst_ip"] == flow.dst_ip]
        same_srv_host = [c for c in last_100 if c["service"] == flow.service]

        dst_host_count = max(1, len(same_dst_host))
        dst_host_srv_count = max(1, sum(1 for c in same_dst_host if c["service"] == flow.service))

        dst_host_same_srv_rate = round(dst_host_srv_count / dst_host_count, 4)
        dst_host_diff_srv_rate = round((dst_host_count - dst_host_srv_count) / dst_host_count, 4)

        host_serrors = sum(1 for c in same_dst_host if c["flag"] in serror_flags)
        host_srv_serrors = sum(
            1 for c in same_dst_host if c["service"] == flow.service and c["flag"] in serror_flags
        )
        host_rerrors = sum(1 for c in same_dst_host if c["flag"] in rerror_flags)

        dst_host_serror_rate = round(host_serrors / dst_host_count, 4)
        dst_host_srv_serror_rate = round(host_srv_serrors / dst_host_srv_count, 4)
        dst_host_rerror_rate = round(host_rerrors / dst_host_count, 4)

        same_src_port_count = sum(1 for c in same_dst_host if c["src_port"] == flow.src_port)
        diff_dst_for_srv = sum(1 for c in same_srv_host if c["dst_ip"] != flow.dst_ip)

        if is_bcast and count <= 30:
            # Broadcast/multicast addresses do not represent a unicast port/host sweep
            dst_host_same_src_port_rate = 0.0
            dst_host_srv_diff_host_rate = 0.0
        else:
            if same_src_port_count <= 1:
                dst_host_same_src_port_rate = round(1.0 / max(dst_host_count, 20), 4)
            else:
                dst_host_same_src_port_rate = round(same_src_port_count / dst_host_count, 4)

            if flag == "SF" and dst_host_serror_rate == 0.0 and dst_host_rerror_rate == 0.0:
                dst_host_srv_diff_host_rate = round(diff_dst_for_srv / max(len(same_srv_host), 25), 4)
            else:
                dst_host_srv_diff_host_rate = round(diff_dst_for_srv / max(1, len(same_srv_host)), 4)

        cur_src_bytes = int(flow.src_bytes)
        cur_dst_bytes = int(flow.dst_bytes)
        cur_total_packets = int(flow.total_packets)

        # Roll flow window if this long-lived flow has exceeded 10s so bytes/duration don't grow unbounded
        if (now - flow.first_seen) >= 10.0 or flow.total_packets >= 50:
            flow.first_seen = now
            flow.src_bytes = 0
            flow.dst_bytes = 0
            flow.fwd_packets = 1 if flow.fwd_packets > 0 else 0
            flow.rev_packets = 1 if flow.rev_packets > 0 else 0
            flow.total_packets = flow.fwd_packets + flow.rev_packets
            flow.emitted_packets = flow.total_packets

        total_bytes = cur_src_bytes + cur_dst_bytes
        eff_duration = duration if duration > 0.05 else 0.05
        packets_per_sec = round(cur_total_packets / eff_duration, 2)
        bytes_per_sec = round(total_bytes / eff_duration, 2)

        features = {
            "duration": duration,
            "protocol_type": flow.protocol,
            "service": flow.service,
            "flag": flag,
            "src_bytes": cur_src_bytes,
            "dst_bytes": cur_dst_bytes,
            "logged_in": int(logged_in),
            "count": int(count),
            "srv_count": int(srv_count),
            "serror_rate": float(serror_rate),
            "srv_serror_rate": float(srv_serror_rate),
            "same_srv_rate": float(same_srv_rate),
            "diff_srv_rate": float(diff_srv_rate),
            "dst_host_count": int(dst_host_count),
            "dst_host_srv_count": int(dst_host_srv_count),
            "dst_host_same_srv_rate": float(dst_host_same_srv_rate),
            "dst_host_diff_srv_rate": float(dst_host_diff_srv_rate),
            "dst_host_same_src_port_rate": float(dst_host_same_src_port_rate),
            "dst_host_srv_diff_host_rate": float(dst_host_srv_diff_host_rate),
            "dst_host_serror_rate": float(dst_host_serror_rate),
            "dst_host_srv_serror_rate": float(dst_host_srv_serror_rate),
            "dst_host_rerror_rate": float(dst_host_rerror_rate),
            "is_broadcast": is_bcast,
        }

        return {
            "source_ip": flow.src_ip,
            "destination_ip": flow.dst_ip,
            "source_port": int(flow.src_port),
            "destination_port": int(flow.dst_port),
            "protocol": flow.protocol.upper(),
            "packet_size": int(total_bytes),
            "packet_count": int(cur_total_packets),
            "flow_duration": float(round(duration, 3)),
            "packets_per_second": float(packets_per_sec),
            "bytes_per_second": float(bytes_per_sec),
            "capture_mode": "REAL",
            "is_broadcast": is_bcast,
            "features": features,
        }


class PacketCaptureAdapter(BaseTrafficAdapter):
    """
    Passive real-time network packet capture adapter using Python Scapy + Npcap.
    Aggregates captured IPv4/IPv6 packets into 5-tuple network flows and extracts
    the 20 NSL-KDD features required by the Random Forest and Decision Tree models.

    Queue Architecture:
    - Uses an explicit queue_capacity (default 2000) with an unbounded deque (maxlen=None)
      so queued flows are NEVER silently evicted.
    - Synchronizes producer threads (Scapy callbacks, periodic flush thread) and the
      consumer worker thread via a shared threading.Condition (self._queue_cond).
    - Overflow policy: bounded backpressure wait up to backpressure_timeout seconds;
      if the queue remains at capacity after backpressure, the incoming flow is explicitly
      rejected (preserving FIFO order of already-queued flows), dropped_flows and
      queue_overflow_events are incremented, and a warning is logged with the reason.
    """
    def __init__(
        self,
        interface: Optional[str] = None,
        queue_capacity: int = 2000,
        backpressure_timeout: float = 0.02,
    ):
        self.aggregator = FlowAggregator()
        self.queue_capacity: int = max(1, int(queue_capacity))
        self.backpressure_timeout: float = max(0.0, float(backpressure_timeout))
        self.ready_flows: deque = deque()  # Explicitly unbounded deque; guarded by self.queue_capacity
        self._sniffer: Optional[Any] = None
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._queue_cond = threading.Condition(self._lock)
        self.persist_lock = threading.Lock()

        self.is_running: bool = False
        self.packets_captured: int = 0
        self.flows_processed: int = 0
        self.max_queue_depth: int = 0
        self.dropped_flows: int = 0
        self.queue_overflow_events: int = 0
        self.total_flows_enqueued: int = 0
        self.total_flows_persisted: int = 0
        self.in_flight_flows: int = 0
        self._total_queue_latency_ms: float = 0.0
        self._max_queue_latency_ms: float = 0.0
        self._latency_samples: int = 0

        self.started_at: Optional[str] = None
        self.last_packet_at: Optional[str] = None
        self.last_error: Optional[str] = None
        self.permission_status: str = "Not started"

        # Auto-select best interface if none provided
        self.available_interfaces = list_network_interfaces()
        self.interface: str = ""
        self.interface_description: str = ""
        self.interface_ip: str = ""
        self.select_interface(interface)

    def select_interface(self, target_interface: Optional[str] = None) -> Dict[str, Any]:
        """Select a network interface by name, description, IP, or NPF device name."""
        self.available_interfaces = list_network_interfaces()
        selected = None

        if target_interface:
            target_lower = target_interface.strip().lower()
            for iface in self.available_interfaces:
                if (
                    iface["name"].lower() == target_lower
                    or iface["description"].lower() == target_lower
                    or iface["network_name"].lower() == target_lower
                    or iface["ip"].lower() == target_lower
                ):
                    selected = iface
                    break
            if not selected:
                for iface in self.available_interfaces:
                    if target_lower in iface["name"].lower() or target_lower in iface["description"].lower():
                        selected = iface
                        break

        if not selected and self.available_interfaces:
            selected = self.available_interfaces[0]

        if selected:
            self.interface = selected["name"]
            self.interface_description = selected["description"]
            self.interface_ip = selected["ip"]
        else:
            self.interface = target_interface or "Wi-Fi"
            self.interface_description = self.interface
            self.interface_ip = "Unknown"

        return selected or {
            "name": self.interface,
            "description": self.interface_description,
            "ip": self.interface_ip,
        }

    def start(self, interface: Optional[str] = None) -> bool:
        """Start passive background packet capture using Scapy AsyncSniffer."""
        if interface:
            self.select_interface(interface)

        if self.is_running:
            self.stop()

        if not SCAPY_AVAILABLE:
            self.last_error = "Scapy is not installed. Run 'pip install scapy'."
            self.permission_status = "ERROR: Scapy unavailable"
            return False

        if not check_npcap_installed():
            self.last_error = (
                "Npcap is not installed or not detected. Please install Npcap from https://npcap.com "
                "with 'Install Npcap in WinPcap API-compatible Mode' enabled."
            )
            self.permission_status = "ERROR: Npcap missing"
            return False

        try:
            with self._queue_cond:
                if self.ready_flows:
                    cleared = len(self.ready_flows)
                    self.ready_flows.clear()
                    self.dropped_flows += cleared
                self._queue_cond.notify_all()
            with self.aggregator._lock:
                self.aggregator.active_flows.clear()

            self._stop_event.clear()
            self.is_running = True
            self._sniffer = AsyncSniffer(
                iface=self.interface,
                prn=self._on_packet,
                store=False,
            )
            self._sniffer.start()
            # Give sniffer thread a brief moment to verify interface open succeeded
            time.sleep(0.15)
            if hasattr(self._sniffer, "exception") and self._sniffer.exception:
                raise self._sniffer.exception

            self.started_at = datetime.now(timezone.utc).isoformat()
            self.last_error = None
            is_admin = check_is_admin()
            self.permission_status = (
                "OK (Administrator Mode + Npcap)"
                if is_admin
                else "OK (Npcap Non-Admin Capture Mode Active)"
            )

            self._flush_thread = threading.Thread(target=self._periodic_flush_loop, daemon=True)
            self._flush_thread.start()
            return True
        except PermissionError as e:
            self.is_running = False
            self._stop_event.set()
            self.last_error = (
                f"Permission denied opening interface '{self.interface}': {e}. "
                "Please run the backend terminal as Administrator or enable non-admin capture in Npcap."
            )
            self.permission_status = "ERROR: Administrator privileges required"
            return False
        except Exception as e:
            self.is_running = False
            self._stop_event.set()
            err_msg = str(e)
            if "permission" in err_msg.lower() or "access is denied" in err_msg.lower():
                self.permission_status = "ERROR: Administrator privileges required"
                self.last_error = (
                    f"Access denied opening '{self.interface}'. Run terminal as Administrator "
                    f"or check Npcap driver permissions. Details: {err_msg}"
                )
            else:
                self.permission_status = f"ERROR: Capture failed ({err_msg})"
                self.last_error = f"Failed to start packet capture on '{self.interface}': {err_msg}"
            return False

    def stop(self):
        """
        Stop passive packet capture immediately, clear pending queued flows and active
        flow aggregation state, and synchronize with the persistence consumer so no
        buffered flows are persisted after Stop completes.
        """
        with self.persist_lock:
            self.is_running = False
            self._stop_event.set()
            if self._sniffer is not None:
                try:
                    if getattr(self._sniffer, "running", False):
                        self._sniffer.stop()
                except Exception:
                    pass
                self._sniffer = None
            with self._queue_cond:
                if self.ready_flows:
                    cleared = len(self.ready_flows)
                    self.ready_flows.clear()
                    self.dropped_flows += cleared
                    logger.info(
                        f"PacketCaptureAdapter.stop(): cleared {cleared} unpersisted queued flows on Stop Sniffer."
                    )
                self._queue_cond.notify_all()
            with self.aggregator._lock:
                self.aggregator.active_flows.clear()

    def enqueue_flow(
        self,
        flow_record: Dict[str, Any],
        block_timeout: Optional[float] = None,
    ) -> bool:
        """
        Thread-safe producer method to enqueue a completed flow record.
        Applies bounded backpressure up to `block_timeout` (defaults to `self.backpressure_timeout`)
        when the queue is at `self.queue_capacity`. Never silently evicts existing queued flows.
        If the queue remains full after backpressure, increments `dropped_flows` and
        `queue_overflow_events`, logs the reason, and returns False.
        """
        timeout = self.backpressure_timeout if block_timeout is None else max(0.0, float(block_timeout))
        with self._queue_cond:
            if not self.is_running or self._stop_event.is_set():
                return False

            self.flows_processed += 1

            if len(self.ready_flows) >= self.queue_capacity and timeout > 0.0:
                deadline = time.perf_counter() + timeout
                while (
                    len(self.ready_flows) >= self.queue_capacity
                    and self.is_running
                    and not self._stop_event.is_set()
                ):
                    remaining = deadline - time.perf_counter()
                    if remaining <= 0.0:
                        break
                    self._queue_cond.wait(timeout=remaining)

            if not self.is_running or self._stop_event.is_set():
                self.dropped_flows += 1
                logger.info(
                    "PacketCaptureAdapter.enqueue_flow(): flow dropped because capture stopped during backpressure wait."
                )
                return False

            if len(self.ready_flows) >= self.queue_capacity:
                self.dropped_flows += 1
                self.queue_overflow_events += 1
                src = flow_record.get("source_ip", "?")
                dst = flow_record.get("destination_ip", "?")
                proto = flow_record.get("protocol", "?")
                logger.warning(
                    f"Flow queue overflow (capacity={self.queue_capacity}, queued={len(self.ready_flows)}, "
                    f"backpressure_timeout={timeout:.3f}s): rejecting incoming flow {src} -> {dst} ({proto}) "
                    f"to preserve FIFO integrity of already-queued flows. "
                    f"dropped_flows={self.dropped_flows}, queue_overflow_events={self.queue_overflow_events}"
                )
                return False

            flow_record["_enqueued_mono"] = time.perf_counter()
            self.ready_flows.append(flow_record)
            self.total_flows_enqueued += 1
            q_len = len(self.ready_flows)
            if q_len > self.max_queue_depth:
                self.max_queue_depth = q_len
            self._queue_cond.notify_all()
            return True

    def _on_packet(self, pkt):
        """Callback invoked by Scapy for every passively captured packet."""
        if not self.is_running or self._stop_event.is_set():
            return
        if IP not in pkt and IPv6 not in pkt:
            return
        if TCP not in pkt and UDP not in pkt and ICMP not in pkt:
            return

        self.packets_captured += 1
        self.last_packet_at = datetime.now(timezone.utc).strftime("%H:%M:%S")

        flow_record = self.aggregator.ingest_packet(pkt)
        if flow_record is not None:
            flow_record["interface"] = self.interface
            self.enqueue_flow(flow_record)

    def _periodic_flush_loop(self):
        """Periodically flush matured flows so low-volume flows are emitted promptly."""
        while not self._stop_event.is_set():
            time.sleep(0.5)
            if not self.is_running or self._stop_event.is_set():
                break
            try:
                flushed = self.aggregator.flush_ready_flows()
                if flushed:
                    for rec in flushed:
                        if not self.is_running or self._stop_event.is_set():
                            break
                        rec["interface"] = self.interface
                        self.enqueue_flow(rec)
            except Exception:
                pass

    def capture_next_packet(self) -> Optional[dict]:
        """Pop the next ready real network flow record if capture is running, or None otherwise."""
        with self._queue_cond:
            if not self.is_running or self._stop_event.is_set():
                if self.ready_flows:
                    cleared = len(self.ready_flows)
                    self.ready_flows.clear()
                    self.dropped_flows += cleared
                    self._queue_cond.notify_all()
                return None
            if self.ready_flows:
                pkt = self.ready_flows.popleft()
                if isinstance(pkt, dict):
                    enq_ts = pkt.pop("_enqueued_mono", None)
                    if enq_ts is not None:
                        lat_ms = max(0.0, (time.perf_counter() - enq_ts) * 1000.0)
                        self._total_queue_latency_ms += lat_ms
                        if lat_ms > self._max_queue_latency_ms:
                            self._max_queue_latency_ms = lat_ms
                        self._latency_samples += 1
                    else:
                        # Normalize accounting if a test appended directly to ready_flows
                        self.flows_processed += 1
                        self.total_flows_enqueued += 1
                        if self.max_queue_depth < 1:
                            self.max_queue_depth = 1
                self.in_flight_flows += 1
                self._queue_cond.notify_all()
                return pkt
        return None

    def mark_flow_persisted(self) -> None:
        """Record that an in-flight flow popped by capture_next_packet() was persisted to SQLite."""
        with self._queue_cond:
            if self.in_flight_flows > 0:
                self.in_flight_flows -= 1
            self.total_flows_persisted += 1

    def mark_flow_failed(self, reason: str = "persistence_error") -> None:
        """Record that an in-flight flow failed during persistence so accounting remains exact."""
        with self._queue_cond:
            if self.in_flight_flows > 0:
                self.in_flight_flows -= 1
            self.dropped_flows += 1
            logger.error(
                f"Flow dropped due to persistence failure ({reason}). dropped_flows={self.dropped_flows}"
            )

    def get_status(self) -> Dict[str, Any]:
        """Return full diagnostic status of the real packet capture engine and queue metrics."""
        sniffer_running = bool(
            self.is_running and self._sniffer is not None and getattr(self._sniffer, "running", True)
        )
        with self._queue_cond:
            queued_flows = len(self.ready_flows)
            queue_capacity = self.queue_capacity
            max_queue_depth = self.max_queue_depth
            dropped_flows = self.dropped_flows
            queue_overflow_events = self.queue_overflow_events
            total_flows_enqueued = self.total_flows_enqueued
            total_flows_persisted = self.total_flows_persisted
            in_flight_flows = self.in_flight_flows
            flows_processed = self.flows_processed
            avg_lat_ms = (
                round(self._total_queue_latency_ms / self._latency_samples, 3)
                if self._latency_samples > 0
                else 0.0
            )
            max_lat_ms = round(self._max_queue_latency_ms, 3)

        return {
            "mode": "REAL",
            "is_running": sniffer_running,
            "active_interface": self.interface,
            "interface_description": self.interface_description,
            "interface_ip": self.interface_ip,
            "packets_captured": self.packets_captured,
            "active_flows": len(self.aggregator.active_flows),
            "flows_processed": flows_processed,
            "queue_capacity": queue_capacity,
            "queued_flows": queued_flows,
            "max_queue_depth": max_queue_depth,
            "dropped_flows": dropped_flows,
            "queue_overflow_events": queue_overflow_events,
            "total_flows_enqueued": total_flows_enqueued,
            "total_flows_persisted": total_flows_persisted,
            "in_flight_flows": in_flight_flows,
            "avg_queue_latency_ms": avg_lat_ms,
            "max_queue_latency_ms": max_lat_ms,
            "scapy_available": SCAPY_AVAILABLE,
            "npcap_available": check_npcap_installed(),
            "is_admin": check_is_admin(),
            "permission_status": self.permission_status,
            "last_error": self.last_error,
            "started_at": self.started_at,
            "last_packet_at": self.last_packet_at,
            "visibility_notice": INTERFACE_VISIBILITY_NOTICE,
        }


class DemoTrafficAdapter(BaseTrafficAdapter):
    """
    Inactive fallback adapter kept only for explicit offline testing when requested.
    Not used in the active live capture pipeline.
    """
    def __init__(self):
        self.is_active = False

    def capture_next_packet(self) -> Optional[dict]:
        return None


# Global singleton real packet capture adapter
real_capture_adapter = PacketCaptureAdapter()
