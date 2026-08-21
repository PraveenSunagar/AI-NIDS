import React, { useState, useEffect } from 'react';
import { alertsApi } from '../services/api';
import { Alert, User } from '../types';
import { SeverityBadge, StatusBadge } from '../components/AlertBadge';
import { ShieldAlert, CheckCircle2, AlertCircle, Filter, Eye, RefreshCw } from 'lucide-react';

interface AlertsProps {
  currentUser: User | null;
}

export const Alerts: React.FC<AlertsProps> = ({ currentUser }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const statusParam = filterStatus !== 'ALL' ? filterStatus : undefined;
      const sevParam = filterSeverity !== 'ALL' ? filterSeverity : undefined;
      const data = await alertsApi.getAlerts(statusParam, sevParam);
      setAlerts(data);
    } catch (e) {
      console.error('Failed to load alerts', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [filterStatus, filterSeverity]);

  const handleUpdateStatus = async (alertId: number, newStatus: 'ACKNOWLEDGED' | 'RESOLVED') => {
    try {
      const updated = await alertsApi.updateStatus(alertId, newStatus);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
      if (selectedAlert && selectedAlert.id === alertId) {
        setSelectedAlert(updated);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Operation failed. Ensure you have ANALYST or ADMIN privileges.');
    }
  };

  const isAuthorizedToEdit = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-soc-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-rose-400" /> Security Alert Management (SOC)
          </h1>
          <p className="text-xs text-slate-400">Review, acknowledge, and resolve security threats triggered by ML detection engine</p>
        </div>

        <button
          onClick={fetchAlerts}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-soc-border text-xs font-mono text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Alerts
        </button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-soc-card p-4 rounded-xl border border-soc-border text-xs">
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          
          <div>
            <span className="text-slate-400 mr-2 font-mono">Status:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-slate-900 border border-soc-border text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open Only</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>

          <div>
            <span className="text-slate-400 mr-2 font-mono">Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="bg-slate-900 border border-soc-border text-slate-200 rounded px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        <div className="font-mono text-slate-400">
          Active Alerts: <strong className="text-rose-400">{alerts.filter(a => a.status === 'OPEN').length}</strong>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="soc-card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-soc-border text-slate-400 font-mono uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Alert ID</th>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4">Attack Category</th>
                <th className="py-3.5 px-4">Source IP</th>
                <th className="py-3.5 px-4">Destination IP</th>
                <th className="py-3.5 px-4">Severity</th>
                <th className="py-3.5 px-4">Confidence</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border/50 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    Loading security alerts...
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No security alerts found matching the criteria.
                  </td>
                </tr>
              ) : (
                alerts.map((alertItem) => (
                  <tr key={alertItem.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-sky-400">#ALT-{alertItem.id}</td>
                    <td className="py-3 px-4 text-slate-400">{new Date(alertItem.created_at).toLocaleString()}</td>
                    <td className="py-3 px-4 text-rose-300 font-semibold">{alertItem.attack_type}</td>
                    <td className="py-3 px-4 text-slate-200">{alertItem.source_ip}</td>
                    <td className="py-3 px-4 text-slate-200">{alertItem.destination_ip}</td>
                    <td className="py-3 px-4">
                      <SeverityBadge severity={alertItem.severity} />
                    </td>
                    <td className="py-3 px-4 text-slate-300">{(alertItem.confidence * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={alertItem.status} />
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => setSelectedAlert(alertItem)}
                        className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-soc-border"
                        title="View Details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>

                      {alertItem.status === 'OPEN' && isAuthorizedToEdit && (
                        <button
                          onClick={() => handleUpdateStatus(alertItem.id, 'ACKNOWLEDGED')}
                          className="px-2 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/40 text-[11px] font-semibold"
                        >
                          Ack
                        </button>
                      )}

                      {alertItem.status !== 'RESOLVED' && isAuthorizedToEdit && (
                        <button
                          onClick={() => handleUpdateStatus(alertItem.id, 'RESOLVED')}
                          className="px-2 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 text-[11px] font-semibold"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alert Details Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-soc-card border border-soc-border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-soc-border pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" /> Alert Details #ALT-{selectedAlert.id}
              </h3>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-slate-400 hover:text-white font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300">
                {selectedAlert.message}
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <span className="text-slate-400 block">Severity:</span>
                  <SeverityBadge severity={selectedAlert.severity} />
                </div>
                <div>
                  <span className="text-slate-400 block">Status:</span>
                  <StatusBadge status={selectedAlert.status} />
                </div>
                <div>
                  <span className="text-slate-400 block">Source IP:</span>
                  <span className="text-slate-200">{selectedAlert.source_ip}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Destination IP:</span>
                  <span className="text-slate-200">{selectedAlert.destination_ip}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Attack Category:</span>
                  <span className="text-slate-200">{selectedAlert.attack_type}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">ML Confidence:</span>
                  <span className="text-sky-400">{(selectedAlert.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>

              {selectedAlert.acknowledged_by && (
                <div className="pt-2 text-[11px] text-slate-400 border-t border-soc-border">
                  Handled by: <strong className="text-slate-200">{selectedAlert.acknowledged_by}</strong> at {new Date(selectedAlert.acknowledged_at || '').toLocaleString()}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-soc-border flex justify-end gap-2 text-xs">
              {selectedAlert.status === 'OPEN' && isAuthorizedToEdit && (
                <button
                  onClick={() => handleUpdateStatus(selectedAlert.id, 'ACKNOWLEDGED')}
                  className="px-3 py-1.5 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded-lg font-semibold hover:bg-amber-500/30"
                >
                  Acknowledge Alert
                </button>
              )}
              {selectedAlert.status !== 'RESOLVED' && isAuthorizedToEdit && (
                <button
                  onClick={() => handleUpdateStatus(selectedAlert.id, 'RESOLVED')}
                  className="px-3 py-1.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-lg font-semibold hover:bg-emerald-500/30"
                >
                  Resolve Alert
                </button>
              )}
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
