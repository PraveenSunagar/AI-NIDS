import axios from 'axios';
import { 
  AuthResponse, 
  User, 
  DashboardStats, 
  TrafficEvent, 
  Alert, 
  MLModelMetrics, 
  AuditLog, 
  DetectionRequestPayload, 
  DetectionResult 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inject Bearer token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('nids_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (name: string, email: string, password: string, role = 'ANALYST'): Promise<User> => {
    const res = await api.post('/auth/register', { name, email, password, role });
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },
};

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const res = await api.get('/dashboard/stats');
    return res.data;
  },
};

export const detectionApi = {
  predict: async (payload: DetectionRequestPayload): Promise<DetectionResult> => {
    const res = await api.post('/detection/predict', payload);
    return res.data;
  },
};

export const alertsApi = {
  getAlerts: async (status?: string, severity?: string): Promise<Alert[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    const res = await api.get(`/alerts?${params.toString()}`);
    return res.data;
  },
  updateStatus: async (alertId: number, status: 'ACKNOWLEDGED' | 'RESOLVED'): Promise<Alert> => {
    const res = await api.put(`/alerts/${alertId}/status`, { status });
    return res.data;
  },
};

export const trafficApi = {
  getHistory: async (limit = 100, prediction?: string, protocol?: string, search?: string): Promise<TrafficEvent[]> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (prediction) params.append('prediction', prediction);
    if (protocol) params.append('protocol', protocol);
    if (search) params.append('search', search);
    const res = await api.get(`/traffic/history?${params.toString()}`);
    return res.data;
  },
};

export const modelsApi = {
  getMetrics: async (): Promise<MLModelMetrics> => {
    const res = await api.get('/models/metrics');
    return res.data;
  },
};

export const logsApi = {
  getAuditLogs: async (action?: string, search?: string): Promise<AuditLog[]> => {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (search) params.append('search', search);
    const res = await api.get(`/logs?${params.toString()}`);
    return res.data;
  },
};

export default api;
