import React, { useEffect, useState } from 'react';
import { dashboardApi } from '../services/api';
import { DashboardStats } from '../types';
import { BarChart3, ShieldAlert, Zap, Layers, RefreshCw } from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts';

export const Analytics: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = () => {
      dashboardApi.getStats().then(setStats).catch(console.error).finally(() => setLoading(false));
    };
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-sky-400 font-mono text-sm">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" /> Loading Security Analytics...
      </div>
    );
  }

  const attackEntries = Object.entries(stats?.attack_distribution || {})
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);
  const primaryThreatVector =
    attackEntries.length > 0 ? `${attackEntries[0][0]} (${attackEntries[0][1]} flows)` : 'None Observed';
  const primaryThreatSubtext =
    attackEntries.length > 0
      ? `Most frequent category in attack_distribution (${stats?.attacks_detected || 0} total flagged flows)`
      : 'No suspicious attack categories observed in database';

  const protoEntries = Object.entries(stats?.protocol_distribution || {})
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);
  const topProtocol =
    protoEntries.length > 0 ? `${protoEntries[0][0]} (${protoEntries[0][1]} flows)` : 'None Observed';
  const topProtocolSubtext =
    protoEntries.length > 0
      ? `Derived from protocol_distribution across ${stats?.total_traffic || 0} captured flows`
      : 'No transport protocol flows recorded yet';

  const timeSeries = stats?.time_series || [];
  const computedMeanConf =
    typeof stats?.recent_mean_confidence === 'number' && timeSeries.length > 0
      ? stats.recent_mean_confidence
      : timeSeries.length > 0
      ? timeSeries.reduce((acc, item) => acc + item.confidence, 0) / timeSeries.length
      : null;
  const meanConfidenceDisplay =
    computedMeanConf !== null ? `${(computedMeanConf * 100).toFixed(1)}%` : 'None Observed';

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-soc-border pb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
          <BarChart3 className="w-6 h-6 text-purple-400" /> Advanced Security & Threat Analytics
        </h1>
        <p className="text-xs text-slate-400">Deep-dive network intrusion attack patterns and protocol vulnerability distributions</p>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="soc-card space-y-2">
          <span className="text-xs text-slate-400 font-medium uppercase">Primary Threat Vector</span>
          <h3 className="text-xl font-bold text-rose-400 font-mono">{primaryThreatVector}</h3>
          <p className="text-xs text-slate-400">{primaryThreatSubtext}</p>
        </div>

        <div className="soc-card space-y-2">
          <span className="text-xs text-slate-400 font-medium uppercase">Most Frequent Protocol</span>
          <h3 className="text-xl font-bold text-sky-400 font-mono">{topProtocol}</h3>
          <p className="text-xs text-slate-400">{topProtocolSubtext}</p>
        </div>

        <div className="soc-card space-y-2">
          <span className="text-xs text-slate-400 font-medium uppercase">Recent-Flow Mean Confidence</span>
          <h3 className="text-xl font-bold text-emerald-400 font-mono">{meanConfidenceDisplay}</h3>
          <p className="text-xs text-slate-400">Mean predicted-class confidence on recent flows (not live accuracy)</p>
        </div>
      </div>

      {/* Analytics Detailed Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" /> Intrusion Frequency Trend
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats?.time_series || []}>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }} />
                <Area type="stepAfter" dataKey="confidence" name="Confidence Score" stroke="#a855f7" fill="#a855f7" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" /> Protocol Intrusion Breakdown
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={Object.entries(stats?.protocol_distribution || {}).map(([p, c]) => ({ protocol: p, count: c }))}>
                <XAxis dataKey="protocol" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="count" name="Flow Count" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
