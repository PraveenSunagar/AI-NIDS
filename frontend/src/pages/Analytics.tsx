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
    dashboardApi.getStats().then(setStats).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-sky-400 font-mono text-sm">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" /> Loading Security Analytics...
      </div>
    );
  }

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
          <h3 className="text-xl font-bold text-rose-400 font-mono">DoS (Denial of Service)</h3>
          <p className="text-xs text-slate-400">High-volume SYN floods (`S0` status flags, elevated connection counts)</p>
        </div>

        <div className="soc-card space-y-2">
          <span className="text-xs text-slate-400 font-medium uppercase">Most Frequent Protocol</span>
          <h3 className="text-xl font-bold text-sky-400 font-mono">TCP / HTTP</h3>
          <p className="text-xs text-slate-400">Main transport protocol observed across network flows</p>
        </div>

        <div className="soc-card space-y-2">
          <span className="text-xs text-slate-400 font-medium uppercase">Average Detection Confidence</span>
          <h3 className="text-xl font-bold text-emerald-400 font-mono">94.8%</h3>
          <p className="text-xs text-slate-400">High precision classification accuracy</p>
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
