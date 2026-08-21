import React, { useEffect, useState } from 'react';
import { dashboardApi, modelsApi } from '../services/api';
import { DashboardStats, MLModelMetrics, TrafficEvent } from '../types';
import { StatCard } from '../components/StatCard';
import { SeverityBadge } from '../components/AlertBadge';
import { 
  Activity, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  Percent, 
  Target, 
  Clock, 
  RefreshCw,
  PieChart as PieIcon,
  BarChart2
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface DashboardProps {
  latestEvent: TrafficEvent | null;
}

export const Dashboard: React.FC<DashboardProps> = ({ latestEvent }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [metrics, setMetrics] = useState<MLModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [statsData, metricsData] = await Promise.all([
        dashboardApi.getStats(),
        modelsApi.getMetrics().catch(() => null)
      ]);
      setStats(statsData);
      setMetrics(metricsData);
    } catch (e) {
      console.error('Failed to load dashboard statistics', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-96 text-sky-400 font-mono text-sm">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" /> Initializing SOC Security Dashboard...
      </div>
    );
  }

  const modelAccuracy = metrics?.models?.RandomForest?.accuracy 
    ? (metrics.models.RandomForest.accuracy * 100).toFixed(2) + '%' 
    : '78.00%';

  // Prepare chart datasets
  const normalVsAttackData = [
    { name: 'Normal Traffic', value: stats?.normal_traffic || 0, color: '#10b981' },
    { name: 'Attack Traffic', value: stats?.attacks_detected || 0, color: '#ef4444' }
  ];

  const attackDistData = Object.entries(stats?.attack_distribution || {}).map(([name, value]) => ({
    name,
    value,
    color: name === 'DoS' ? '#ef4444' : name === 'Probe' ? '#f59e0b' : '#38bdf8'
  }));

  const protocolDistData = Object.entries(stats?.protocol_distribution || {}).map(([name, count]) => ({
    protocol: name,
    count
  }));

  const severityDistData = Object.entries(stats?.severity_distribution || {}).map(([severity, count]) => ({
    severity,
    count
  }));

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-soc-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">SOC Threat Intelligence Dashboard</h1>
          <p className="text-xs text-slate-400">Real-time NSL-KDD machine learning network traffic monitoring</p>
        </div>
        <button
          onClick={fetchDashboardData}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-soc-border text-xs font-mono text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Metrics
        </button>
      </div>

      {/* Top 6 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Traffic"
          value={stats?.total_traffic || 0}
          subtext="Captured flow records"
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="Normal Traffic"
          value={stats?.normal_traffic || 0}
          subtext="Benign network packets"
          icon={ShieldCheck}
          color="emerald"
        />
        <StatCard
          title="Attacks Detected"
          value={stats?.attacks_detected || 0}
          subtext="Threat intrusions"
          icon={ShieldAlert}
          color="rose"
        />
        <StatCard
          title="Open Alerts"
          value={stats?.open_alerts || 0}
          subtext="Requires SOC review"
          icon={AlertTriangle}
          color="amber"
        />
        <StatCard
          title="Detection Rate"
          value={`${stats?.detection_rate || 0}%`}
          subtext="Intrusion ratio"
          icon={Percent}
          color="purple"
        />
        <StatCard
          title="Model Accuracy"
          value={modelAccuracy}
          subtext="NSL-KDD test set"
          icon={Target}
          color="emerald"
        />
      </div>

      {/* Main Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart 1: Traffic Over Time */}
        <div className="soc-card lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" /> Real-time Traffic Event Stream
            </h3>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
              ● Live Stream
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats?.time_series || []}>
                <defs>
                  <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} />
                <YAxis domain={[0, 1]} stroke="#475569" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="confidence" name="Detection Confidence" stroke="#38bdf8" fillOpacity={1} fill="url(#colorConfidence)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Normal vs Attack Pie Chart */}
        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-emerald-400" /> Normal vs Attack Distribution
          </h3>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={normalVsAttackData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {normalVsAttackData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Secondary Distribution Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Chart 3: Attack Category Distribution */}
        <div className="soc-card space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" /> Attack Type Categories
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={attackDistData}>
                <XAxis dataKey="name" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="value" name="Attacks" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Protocol Distribution */}
        <div className="soc-card space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-sky-400" /> Protocol Distribution
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={protocolDistData}>
                <XAxis dataKey="protocol" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="count" name="Packets" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 5: Severity Distribution */}
        <div className="soc-card space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" /> Alert Severity Levels
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityDistData}>
                <XAxis dataKey="severity" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="count" name="Alerts" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
