import random
import time
from abc import ABC, abstractmethod
from datetime import datetime

class BaseTrafficAdapter(ABC):
    @abstractmethod
    def capture_next_packet(self) -> dict:
        """Capture or generate the next traffic record features dictionary."""
        pass

class DemoTrafficAdapter(BaseTrafficAdapter):
    """
    Simulates real-time network traffic with configurable attack ratio and realistic IP/feature profiles.
    """
    def __init__(self, attack_ratio: float = 0.25):
        self.attack_ratio = attack_ratio
        self.protocols = ["tcp", "udp", "icmp"]
        self.services = ["http", "smtp", "ftp", "private", "domain_u", "eco_i", "other"]
        self.flags = ["SF", "S0", "REJ", "RSTR", "SH"]
        self.src_ips = [f"192.168.1.{i}" for i in range(10, 50)] + ["10.0.0.45", "172.16.0.88", "45.33.22.11"]
        self.dst_ips = ["192.168.1.1", "192.168.1.100", "10.0.0.1", "172.16.0.1"]

    def capture_next_packet(self) -> dict:
        is_attack = random.random() < self.attack_ratio
        protocol = random.choice(self.protocols)
        service = random.choice(self.services)
        src_ip = random.choice(self.src_ips)
        dst_ip = random.choice(self.dst_ips)

        if is_attack:
            attack_profile = random.choice(["DoS", "Probe", "R2L"])
            if attack_profile == "DoS":
                flag = random.choice(["S0", "REJ"])
                duration = random.uniform(0, 5)
                src_bytes = random.choice([0, 100000])
                dst_bytes = random.choice([0, 50000])
                count = random.randint(150, 400)
                srv_count = random.randint(10, 200)
                serror_rate = random.uniform(0.7, 1.0)
                same_srv_rate = random.uniform(0.0, 0.2)
                diff_srv_rate = random.uniform(0.5, 1.0)
                dst_host_count = 255
                dst_host_srv_count = random.randint(1, 30)
                dst_host_same_srv_rate = random.uniform(0.0, 0.2)
                dst_host_diff_srv_rate = random.uniform(0.6, 1.0)
                dst_host_same_src_port_rate = random.uniform(0.0, 0.3)
                dst_host_srv_diff_host_rate = 0.0
                dst_host_serror_rate = random.uniform(0.7, 1.0)
                dst_host_srv_serror_rate = random.uniform(0.7, 1.0)
                dst_host_rerror_rate = 0.0
            elif attack_profile == "Probe":
                flag = "REJ"
                duration = random.uniform(0, 2)
                src_bytes = 0
                dst_bytes = 0
                count = random.randint(50, 200)
                srv_count = random.randint(1, 10)
                serror_rate = 0.0
                same_srv_rate = random.uniform(0.0, 0.1)
                diff_srv_rate = random.uniform(0.8, 1.0)
                dst_host_count = 255
                dst_host_srv_count = random.randint(1, 10)
                dst_host_same_srv_rate = 0.05
                dst_host_diff_srv_rate = 0.95
                dst_host_same_src_port_rate = random.uniform(0.5, 1.0)
                dst_host_srv_diff_host_rate = random.uniform(0.2, 0.8)
                dst_host_serror_rate = 0.0
                dst_host_srv_serror_rate = 0.0
                dst_host_rerror_rate = random.uniform(0.5, 1.0)
            else: # R2L
                flag = "SF"
                duration = random.uniform(10, 100)
                src_bytes = random.randint(500, 3000)
                dst_bytes = random.randint(200, 1500)
                count = 1
                srv_count = 1
                serror_rate = 0.0
                same_srv_rate = 1.0
                diff_srv_rate = 0.0
                dst_host_count = random.randint(1, 50)
                dst_host_srv_count = random.randint(1, 50)
                dst_host_same_srv_rate = 1.0
                dst_host_diff_srv_rate = 0.0
                dst_host_same_src_port_rate = 0.1
                dst_host_srv_diff_host_rate = 0.0
                dst_host_serror_rate = 0.0
                dst_host_srv_serror_rate = 0.0
                dst_host_rerror_rate = 0.0
            logged_in = 0
        else: # NORMAL
            flag = "SF"
            duration = random.uniform(0.1, 10.0)
            src_bytes = random.randint(200, 5000)
            dst_bytes = random.randint(500, 15000)
            count = random.randint(1, 15)
            srv_count = random.randint(1, 15)
            serror_rate = 0.0
            same_srv_rate = 1.0
            diff_srv_rate = 0.0
            dst_host_count = random.randint(10, 200)
            dst_host_srv_count = random.randint(50, 255)
            dst_host_same_srv_rate = random.uniform(0.85, 1.0)
            dst_host_diff_srv_rate = random.uniform(0.0, 0.1)
            dst_host_same_src_port_rate = random.uniform(0.0, 0.3)
            dst_host_srv_diff_host_rate = random.uniform(0.0, 0.1)
            dst_host_serror_rate = 0.0
            dst_host_srv_serror_rate = 0.0
            dst_host_rerror_rate = 0.0
            logged_in = 1

        packet_size = src_bytes + dst_bytes if (src_bytes + dst_bytes) > 0 else random.randint(64, 1500)
        packets_per_sec = round(count / (duration if duration > 0 else 1.0), 2)
        bytes_per_sec = round(packet_size / (duration if duration > 0 else 1.0), 2)

        return {
            "source_ip": src_ip,
            "destination_ip": dst_ip,
            "source_port": random.randint(1024, 65535),
            "destination_port": 80 if service == "http" else (443 if service == "ssl" else random.randint(20, 1000)),
            "protocol": protocol,
            "packet_size": packet_size,
            "flow_duration": round(duration, 2),
            "packets_per_second": packets_per_sec,
            "bytes_per_second": bytes_per_sec,
            "features": {
                "duration": duration,
                "protocol_type": protocol,
                "service": service,
                "flag": flag,
                "src_bytes": src_bytes,
                "dst_bytes": dst_bytes,
                "logged_in": logged_in,
                "count": count,
                "srv_count": srv_count,
                "serror_rate": serror_rate,
                "same_srv_rate": same_srv_rate,
                "diff_srv_rate": diff_srv_rate,
                "dst_host_count": dst_host_count,
                "dst_host_srv_count": dst_host_srv_count,
                "dst_host_same_srv_rate": dst_host_same_srv_rate,
                "dst_host_diff_srv_rate": dst_host_diff_srv_rate,
                "dst_host_same_src_port_rate": dst_host_same_src_port_rate,
                "dst_host_srv_diff_host_rate": dst_host_srv_diff_host_rate,
                "dst_host_serror_rate": dst_host_serror_rate,
                "dst_host_srv_serror_rate": dst_host_srv_serror_rate
            }
        }

class PacketCaptureAdapter(BaseTrafficAdapter):
    """
    Adapter stub for actual network interface packet capture (e.g. via Scapy or PCAP library).
    Requires root/administrator privileges and network interface configuration.
    """
    def __init__(self, interface: str = "eth0"):
        self.interface = interface
        self.is_active = False

    def capture_next_packet(self) -> dict:
        raise NotImplementedError(
            f"Live packet capture on interface '{self.interface}' requires administrative privileges and Scapy/libpcap environment configuration. Use DemoTrafficAdapter for simulated traffic."
        )
