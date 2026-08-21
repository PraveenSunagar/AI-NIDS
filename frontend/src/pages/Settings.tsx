import React, { useState } from 'react';
import { Settings as SettingsIcon, Shield, Radio, Flame, Server, AlertTriangle, CheckCircle } from 'lucide-react';

export const Settings: React.FC = () => {
  const [trafficMode, setTrafficMode] = useState<'DEMO' | 'LIVE'>('DEMO');
  const [highThreshold, setHighThreshold] = useState(0.85);
  const [criticalThreshold, setCriticalThreshold] = useState(0.92);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Title */}
      <div className="border-b border-soc-border pb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-sky-400" /> System Configuration & Integration Guidelines
        </h1>
        <p className="text-xs text-slate-400 font-mono">Manage traffic capture adapters, alert thresholds, and firewall/SIEM integration policies</p>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4" /> System configuration updated successfully.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Adapter Mode Configuration */}
        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-soc-border pb-2">
            <Radio className="w-4 h-4 text-sky-400" /> Network Traffic Adapter Mode
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              onClick={() => setTrafficMode('DEMO')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                trafficMode === 'DEMO'
                  ? 'bg-sky-500/10 border-sky-500/50 text-white'
                  : 'bg-slate-900/60 border-soc-border text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between font-bold text-xs mb-1">
                <span>Demo Simulated Traffic</span>
                {trafficMode === 'DEMO' && <span className="text-sky-400">ACTIVE</span>}
              </div>
              <p className="text-xs text-slate-400">
                Continuous generation of realistic packet streams over WebSockets. Ideal for development, testing, and presentation demonstrations.
              </p>
            </div>

            <div
              onClick={() => setTrafficMode('LIVE')}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                trafficMode === 'LIVE'
                  ? 'bg-amber-500/10 border-amber-500/50 text-white'
                  : 'bg-slate-900/60 border-soc-border text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between font-bold text-xs mb-1">
                <span>Live Packet Capture (Scapy / PCAP)</span>
                {trafficMode === 'LIVE' && <span className="text-amber-400">ACTIVE</span>}
              </div>
              <p className="text-xs text-slate-400">
                Requires network adapter interface configuration (e.g. `eth0`, `wlan0`) and system administrator / root privileges.
              </p>
            </div>
          </div>
        </div>

        {/* Configurable Alert Thresholds */}
        <div className="soc-card space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-soc-border pb-2">
            <Flame className="w-4 h-4 text-amber-400" /> Alert Severity Confidence Thresholds
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
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
              <span className="text-[11px] text-slate-400 mt-1 block">Detections above this confidence are labeled HIGH severity</span>
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
              <span className="text-[11px] text-slate-400 mt-1 block">Detections above this confidence are labeled CRITICAL severity</span>
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
            <AlertTriangle className="w-4 h-4" /> System Scope & Technical Limitations Notice
          </div>
          <ul className="list-disc list-inside text-slate-400 space-y-1">
            <li><strong>Dataset Scope:</strong> Models are trained on the NSL-KDD benchmark dataset (41 traffic features, 20 key features selected).</li>
            <li><strong>Live Packet Capture:</strong> Actual packet capture requires appropriate network access permissions and packet sniffer interface configuration.</li>
            <li><strong>Zero-Day Attacks:</strong> Supervised classification detects patterns present in training data; novel zero-day attacks require future unsupervised anomaly detection models.</li>
          </ul>
        </div>

        <button
          type="submit"
          className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-md shadow-sky-500/20"
        >
          Save Configuration Changes
        </button>
      </form>
    </div>
  );
};
