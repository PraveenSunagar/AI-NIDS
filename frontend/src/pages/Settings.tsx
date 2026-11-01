import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Radio, Flame, Server, AlertTriangle, CheckCircle, Wifi, RefreshCw } from 'lucide-react';
import { trafficApi, alertsApi } from '../services/api';
import { CaptureStatus, NetworkInterfaceInfo } from '../types';

export const Settings: React.FC = () => {
  const [captureStatus, setCaptureStatus] = useState<CaptureStatus | null>(null);
  const [interfaces, setInterfaces] = useState<NetworkInterfaceInfo[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string>('');
  const [dedupWindowSeconds, setDedupWindowSeconds] = useState<number>(120);
  const [highThreshold, setHighThreshold] = useState(0.82);
  const [criticalThreshold, setCriticalThreshold] = useState(0.90);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchCaptureSettings = async () => {
    try {
      const [ifaceData, statusData, alertCfg] = await Promise.all([
        trafficApi.getInterfaces(),
        trafficApi.getCaptureStatus(),
        alertsApi.getConfig().catch(() => ({ dedup_window_seconds: 120, unverified_confidence_threshold: 0.72 }))
      ]);
      setInterfaces(ifaceData.interfaces || []);
      setCaptureStatus(statusData);
      setSelectedInterface(statusData.active_interface || '');
      setDedupWindowSeconds(alertCfg.dedup_window_seconds);
    } catch (e) {
      console.error('Failed to load capture settings', e);
    }
  };

  useEffect(() => {
    fetchCaptureSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const [updated] = await Promise.all([
        trafficApi.configureCapture(selectedInterface, 'restart'),
        alertsApi.updateConfig(dedupWindowSeconds)
      ]);
      setCaptureStatus(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to apply capture configuration', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Title */}
      <div className="border-b border-soc-border pb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-sky-400" /> System Configuration & Live Capture Settings
        </h1>
        <p className="text-xs text-slate-400 font-mono">
          Manage Scapy/Npcap network interfaces, passive flow capture state, and SOC alert policies
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4" /> Real packet capture interface and configuration updated successfully.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Adapter Mode & Interface Configuration */}
        <div className="soc-card space-y-4">
          <div className="flex items-center justify-between border-b border-soc-border pb-2">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-emerald-400" /> Network Traffic Capture Engine (REAL MODE)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
              {captureStatus?.is_running ? 'REAL CAPTURE ACTIVE' : 'REAL CAPTURE STOPPED'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border bg-emerald-500/10 border-emerald-500/50 text-white">
              <div className="flex items-center justify-between font-bold text-xs mb-1">
                <span>Real Passive Packet Capture (Scapy + Npcap)</span>
                <span className="text-emerald-400 font-mono">ACTIVE PIPELINE</span>
              </div>
              <p className="text-xs text-slate-300">
                Passively sniffs live IPv4/IPv6 packets on your selected Windows Wi-Fi or Ethernet adapter, aggregates 5-tuple flows, and extracts 20 NSL-KDD features for real-time Random Forest / Decision Tree inference.
              </p>
            </div>

            <div className="p-4 rounded-xl border bg-slate-900/60 border-soc-border text-slate-400 opacity-75">
              <div className="flex items-center justify-between font-bold text-xs mb-1">
                <span>Demo Simulated Traffic (DemoTrafficAdapter)</span>
                <span className="text-slate-500 font-mono">REMOVED FROM LIVE PIPELINE</span>
              </div>
              <p className="text-xs text-slate-400">
                Synthetic traffic generation and fixed attack ratios are disabled in the live pipeline so all alerts and telemetry reflect real network flows.
              </p>
            </div>
          </div>

          {/* Interface Selector & Diagnostics */}
          <div className="pt-2 space-y-3 text-xs font-mono">
            <div>
              <label className="block text-slate-300 font-sans font-medium mb-1.5 flex items-center gap-1.5">
                <Wifi className="w-4 h-4 text-sky-400" /> Select Active Network Interface (Windows Npcap):
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={selectedInterface}
                  onChange={(e) => setSelectedInterface(e.target.value)}
                  className="w-full bg-slate-900 border border-soc-border rounded-lg px-3 py-2 text-white"
                >
                  {interfaces.map((iface) => (
                    <option key={iface.network_name || iface.name} value={iface.name}>
                      [{iface.type}] {iface.name} — {iface.description} (IP: {iface.ip})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={fetchCaptureSettings}
                  className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-soc-border text-slate-200 flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Refresh
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-slate-900/90 border border-soc-border">
                <span className="text-slate-400 block text-[11px]">Npcap Driver Status</span>
                <span className={captureStatus?.npcap_available ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                  {captureStatus?.npcap_available ? 'Available (WinPcap/Npcap)' : 'Not Detected'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/90 border border-soc-border">
                <span className="text-slate-400 block text-[11px]">Permission Status</span>
                <span className="text-sky-400 font-bold">
                  {captureStatus?.permission_status || 'Checking...'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/90 border border-soc-border">
                <span className="text-slate-400 block text-[11px]">Packets / Flows Captured</span>
                <span className="text-white font-bold">
                  {captureStatus?.packets_captured || 0} pkts / {captureStatus?.flows_processed || 0} flows
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Configurable Alert Deduplication & Thresholds */}
        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-soc-border pb-2">
            <Flame className="w-4 h-4 text-amber-400" /> Alert Deduplication & Severity Validation Policy
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Deduplication Window (Seconds)</label>
              <input
                type="number"
                step="10"
                min="0"
                max="3600"
                value={dedupWindowSeconds}
                onChange={(e) => setDedupWindowSeconds(parseInt(e.target.value, 10) || 0)}
                className="w-full bg-slate-900 border border-soc-border rounded px-3 py-2 text-white font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Repeated flows matching (Source IP, Dest IP, Attack Type) within this window are merged</span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">HIGH Severity Threshold</label>
              <input
                type="number"
                step="0.01"
                min="0.50"
                max="0.99"
                value={highThreshold}
                onChange={(e) => setHighThreshold(parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-soc-border rounded px-3 py-2 text-white font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Verified detections (&ge;72%) above this confidence with scan/flood indicators</span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">CRITICAL Severity Threshold</label>
              <input
                type="number"
                step="0.01"
                min="0.50"
                max="0.99"
                value={criticalThreshold}
                onChange={(e) => setCriticalThreshold(parseFloat(e.target.value))}
                className="w-full bg-slate-900 border border-soc-border rounded px-3 py-2 text-white font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">Verified detections above this confidence with severe flood/exploit indicators</span>
            </div>
          </div>
        </div>

        {/* Future Integration Panel */}
        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-soc-border pb-2">
            <Server className="w-4 h-4 text-purple-400" /> SIEM & Firewall Integration Recommended Actions
          </h3>

          <p className="text-xs text-slate-400">
            For safe operation, automatic destructive firewall blocking is disabled by default. When an attack is flagged, the system recommends the following SOC operator responses:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-900/80 rounded-lg border border-soc-border space-y-1">
              <span className="font-bold text-sky-400">1. Investigate Source IP</span>
              <p className="text-slate-400">Perform WHOIS and threat intelligence lookup on offending IP address.</p>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-lg border border-soc-border space-y-1">
              <span className="font-bold text-rose-400">2. Block Source IP (Firewall Rule)</span>
              <p className="text-slate-400">Export iptables / pfSense block rule upon analyst authorization.</p>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-lg border border-soc-border space-y-1">
              <span className="font-bold text-amber-400">3. Increase Monitoring Depth</span>
              <p className="text-slate-400">Lower logging interval for suspicious subnet traffic flows.</p>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-lg border border-soc-border space-y-1">
              <span className="font-bold text-emerald-400">4. Forward Event to SIEM</span>
              <p className="text-slate-400">Export Syslog / CEF audit log entries to Splunk or Elastic SIEM.</p>
            </div>
          </div>
        </div>

        {/* Limitations Notice */}
        <div className="soc-card bg-slate-900/90 border-amber-500/30 p-4 space-y-2 text-xs">
          <div className="flex items-center gap-2 font-bold text-amber-400">
            <AlertTriangle className="w-4 h-4" /> Interface Visibility & Technical Scope Notice
          </div>
          <ul className="list-disc list-inside text-slate-400 space-y-1">
            <li><strong>Interface Visibility Limitation:</strong> Passive capture on a standard Windows Wi-Fi or Ethernet NIC captures traffic sent to/from this host and broadcast/multicast frames. It does <em>not</em> capture unicast traffic between other separate devices on a switched network or encrypted Wi-Fi AP unless switch port mirroring (SPAN) or an inline tap is configured.</li>
            <li><strong>Passive Only:</strong> The sniffer operates strictly in passive receive mode (`store=False`) and never injects, transmits, or crafts network packets.</li>
            <li><strong>NSL-KDD Feature Mapping:</strong> Real packets are aggregated into 5-tuple flows and mapped to the 20 NSL-KDD features evaluated by the Random Forest and Decision Tree models.</li>
          </ul>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-md shadow-sky-500/20 disabled:opacity-50"
        >
          {loading ? 'Applying Interface & Capture Settings...' : 'Apply Interface & Save Configuration'}
        </button>
      </form>
    </div>
  );
};
