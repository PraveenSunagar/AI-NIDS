import React, { useState, useEffect } from 'react';
import { logsApi, trafficApi } from '../services/api';
import { AuditLog, TrafficEvent } from '../types';
import { FileText, Search, Activity, ShieldCheck, RefreshCw } from 'lucide-react';

export const TrafficLogs: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'audit' | 'traffic'>('audit');
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [trafficLogs, setTrafficLogs] = useState<TrafficEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      if (activeSubTab === 'audit') {
        const data = await logsApi.getAuditLogs(undefined, search);
        setAuditLogs(data);
      } else {
        const data = await trafficApi.getHistory(100, undefined, undefined, search);
        setTrafficLogs(data);
      }
    } catch (e) {
      console.error('Failed to load logs', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [activeSubTab, search]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-soc-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-sky-400" /> Security Audit & Traffic Logs
          </h1>
          <p className="text-xs text-slate-400">Structured system audit trail and historical packet prediction logs</p>
        </div>

        <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-lg border border-soc-border text-xs">
          <button
            onClick={() => setActiveSubTab('audit')}
            className={`px-3 py-1.5 rounded-md font-semibold transition-all ${
              activeSubTab === 'audit' ? 'bg-sky-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Audit Trail
          </button>
          <button
            onClick={() => setActiveSubTab('traffic')}
            className={`px-3 py-1.5 rounded-md font-semibold transition-all ${
              activeSubTab === 'traffic' ? 'bg-sky-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Traffic History
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-soc-card p-4 rounded-xl border border-soc-border flex items-center justify-between">
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={activeSubTab === 'audit' ? "Search User, Action, Endpoint..." : "Search IP, Protocol, Attack..."}
            className="w-full pl-10 pr-4 py-1.5 bg-slate-900 border border-soc-border rounded-lg text-xs text-white focus:outline-none focus:border-sky-500"
          />
        </div>

        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-soc-border text-xs font-mono text-slate-300"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {/* Logs Data Table */}
      <div className="soc-card overflow-hidden p-0">
        <div className="overflow-x-auto">
          {activeSubTab === 'audit' ? (
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-soc-border text-slate-400 font-mono uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Log ID</th>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">User</th>
                  <th className="py-3.5 px-4">Action Event</th>
                  <th className="py-3.5 px-4">Endpoint</th>
                  <th className="py-3.5 px-4">Client IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-soc-border/50 font-mono">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">No audit entries found.</td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-bold text-sky-400">#{log.id}</td>
                      <td className="py-3 px-4 text-slate-400">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="py-3 px-4 text-slate-200">{log.user_email}</td>
                      <td className="py-3 px-4 text-emerald-400 font-semibold">{log.action}</td>
                      <td className="py-3 px-4 text-slate-400">{log.endpoint || 'System'}</td>
                      <td className="py-3 px-4 text-slate-300">{log.ip_address}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-soc-border text-slate-400 font-mono uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">ID</th>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Flow IPs</th>
                  <th className="py-3.5 px-4">Protocol</th>
                  <th className="py-3.5 px-4">Prediction</th>
                  <th className="py-3.5 px-4">Attack Type</th>
                  <th className="py-3.5 px-4">Confidence</th>
                  <th className="py-3.5 px-4">Classifier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-soc-border/50 font-mono">
                {trafficLogs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">No traffic logs found.</td>
                  </tr>
                ) : (
                  trafficLogs.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 text-slate-400">#{t.id}</td>
                      <td className="py-3 px-4 text-slate-400">{t.timestamp}</td>
                      <td className="py-3 px-4 text-slate-200">{t.source_ip} → {t.destination_ip}</td>
                      <td className="py-3 px-4 text-sky-400 font-bold">{t.protocol}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          t.prediction === 'ATTACK' ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {t.prediction}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-200">{t.attack_type}</td>
                      <td className="py-3 px-4 text-slate-300">{(t.confidence * 100).toFixed(1)}%</td>
                      <td className="py-3 px-4 text-slate-400">{t.model_name}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
