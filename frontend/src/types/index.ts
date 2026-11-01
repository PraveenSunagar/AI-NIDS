export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface NetworkInterfaceInfo {
  name: string;
  description: string;
  ip: string;
  mac: string;
  network_name: string;
  type: string;
  is_active_lan: boolean;
  priority: number;
}

export interface CaptureStatus {
  mode: 'REAL' | 'DEMO';
  is_running: boolean;
  active_interface: string;
  interface_description: string;
  interface_ip: string;
  packets_captured: number;
  active_flows: number;
  flows_processed: number;
  queue_capacity?: number;
  queued_flows?: number;
  max_queue_depth?: number;
  dropped_flows?: number;
  queue_overflow_events?: number;
  total_flows_enqueued?: number;
  total_flows_persisted?: number;
  in_flight_flows?: number;
  avg_queue_latency_ms?: number;
  max_queue_latency_ms?: number;
  scapy_available: boolean;
  npcap_available: boolean;
  is_admin: boolean;
  permission_status: string;
  last_error: string | null;
  started_at: string | null;
  last_packet_at: string | null;
  visibility_notice: string;
}

export interface InterfacesResponse {
  interfaces: NetworkInterfaceInfo[];
  active_interface: string;
  scapy_available: boolean;
  npcap_available: boolean;
  is_admin: boolean;
  visibility_notice: string;
}

export interface TrafficEvent {
  id: number;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  source_port: number;
  destination_port: number;
  protocol: string;
  packet_size: number;
  packet_count?: number;
  flow_duration?: number;
  packets_per_second?: number;
  bytes_per_second?: number;
  interface?: string;
  capture_mode?: 'REAL' | 'DEMO' | 'MANUAL_TEST';
  prediction: 'NORMAL' | 'ATTACK';
  attack_type: string;
  confidence: number;
  model_name: string;
  severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'NORMAL';
  validation_status?: 'NORMAL' | 'VERIFIED_BENIGN_BROADCAST' | 'UNVERIFIED' | 'VERIFIED_SUSPICIOUS' | string;
  evidence?: string[];
  feature_data?: Record<string, any>;
  capture_status?: CaptureStatus;
}

export interface Alert {
  id: number;
  traffic_record_id?: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  attack_type: string;
  source_ip: string;
  destination_ip: string;
  message: string;
  confidence: number;
  status: 'UNVERIFIED' | 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  created_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  validation_status?: string;
  evidence?: string[];
  occurrence_count?: number;
}

export interface DashboardStats {
  total_traffic: number;
  normal_traffic: number;
  attacks_detected: number;
  open_alerts: number;
  detection_rate: number;
  recent_mean_confidence?: number;
  protocol_distribution: Record<string, number>;
  attack_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  time_series: Array<{
    time: string;
    prediction: string;
    confidence: number;
    attack_type: string;
    protocol: string;
  }>;
  capture_status?: CaptureStatus;
}

export interface MLModelMetrics {
  dataset_name: string;
  feature_count: number;
  training_date: string;
  selected_model: string;
  features: string[];
  feature_importance: Record<string, number>;
  models: {
    DecisionTree?: {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      confusion_matrix: {
        true_normal: number;
        false_attack: number;
        false_normal: number;
        true_attack: number;
      };
    };
    RandomForest?: {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      confusion_matrix: {
        true_normal: number;
        false_attack: number;
        false_normal: number;
        true_attack: number;
      };
    };
  };
}

export interface AuditLog {
  id: number;
  user_id?: number;
  user_email: string;
  action: string;
  endpoint?: string;
  ip_address?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface DetectionRequestPayload {
  duration: number;
  protocol_type: string;
  service: string;
  flag: string;
  src_bytes: number;
  dst_bytes: number;
  logged_in: number;
  count: number;
  srv_count: number;
  serror_rate: number;
  srv_serror_rate: number;
  same_srv_rate: number;
  diff_srv_rate: number;
  dst_host_count: number;
  dst_host_srv_count: number;
  dst_host_same_srv_rate: number;
  dst_host_diff_srv_rate: number;
  dst_host_same_src_port_rate: number;
  dst_host_srv_diff_host_rate: number;
  dst_host_serror_rate: number;
  dst_host_srv_serror_rate: number;
  dst_host_rerror_rate: number;
  model_name?: string;
}

export interface DetectionResult {
  id?: number;
  prediction: 'NORMAL' | 'ATTACK';
  attack_type: string;
  confidence: number;
  model_name: string;
  timestamp: string;
  alert_created: boolean;
}
