from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class DetectionRequest(BaseModel):
    duration: float = Field(0.0, description="Duration of connection in seconds")
    protocol_type: str = Field("tcp", description="Protocol type: tcp, udp, icmp")
    service: str = Field("http", description="Network service e.g. http, smtp, ftp")
    flag: str = Field("SF", description="Connection status flag e.g. SF, S0, REJ")
    src_bytes: int = Field(250, description="Source to destination bytes")
    dst_bytes: int = Field(1200, description="Destination to source bytes")
    logged_in: int = Field(1, description="1 if successfully logged in; 0 otherwise")
    count: int = Field(5, description="Number of connections to the same host as current connection in past 2s")
    srv_count: int = Field(5, description="Number of connections to the same service in past 2s")
    serror_rate: float = Field(0.0, description="% of connections that have SYN errors")
    same_srv_rate: float = Field(1.0, description="% of connections to the same service")
    diff_srv_rate: float = Field(0.0, description="% of connections to different services")
    dst_host_count: int = Field(100, description="Destination host count")
    dst_host_srv_count: int = Field(250, description="Destination host service count")
    dst_host_same_srv_rate: float = Field(1.0, description="Destination host same service rate")
    dst_host_diff_srv_rate: float = Field(0.0, description="Destination host diff service rate")
    dst_host_same_src_port_rate: float = Field(0.1, description="Destination host same source port rate")
    dst_host_srv_diff_host_rate: float = Field(0.0, description="Destination host service diff host rate")
    dst_host_serror_rate: float = Field(0.0, description="Destination host SYN error rate")
    dst_host_srv_serror_rate: float = Field(0.0, description="Destination host service SYN error rate")
    model_name: Optional[str] = Field("best", description="Model name to use: best, DecisionTree, RandomForest")

class DetectionResponse(BaseModel):
    id: Optional[int] = None
    prediction: str  # NORMAL / ATTACK
    attack_type: str
    confidence: float
    model_name: str
    timestamp: str
    alert_created: bool = False
    alert_severity: Optional[str] = None
