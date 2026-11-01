import React, { useState, useEffect } from 'react';
import { TrafficEvent, CaptureStatus, NetworkInterfaceInfo } from '../types';
import { SeverityBadge } from '../components/AlertBadge';
import {
  Activity,
  Play,
  Pause,
  Download,
  Search,
  Filter,
  Wifi,
  Radio,
  ShieldAlert,
  Info,
  RefreshCw,
  Layers,
  Cpu
} from 'lucide-react';
import { trafficApi } from '../services/api';

interface LiveTrafficProps {
  latestEvent: TrafficEvent | null;
  isWsConnected: boolean;
  captureStatus?: CaptureStatus | null;
  onCaptureStatusChange?: (status: CaptureStatus) => void;
}

const formatEndpoint = (ip: string, port?: number): string => {
  if (!ip) return '';
  const hasPort = typeof port === 'number' && port > 0;
  if (ip.includes(':')) {
    return hasPort ? `[${ip}]:${port}` : `[${ip}]`;
  }
  return hasPort ? `${ip}:${port}` : ip;
};

const formatProtocolDisplay = (protocol: string, srcPort?: number, dstPort?: number): string => {
  const protoUpper = (protocol || '').toUpperCase();
  if (protoUpper === 'UDP' && (srcPort === 443 || dstPort === 443)) {
    return 'UDP/443 (QUIC)';
  }
  return protoUpper;
};

export const LiveTraffic: React.FC<LiveTrafficProps> = ({
  latestEvent,
  isWsConnected,
  captureStatus: parentCaptureStatus,
  onCaptureStatusChange
}) => {
  const [trafficList, setTrafficList] = useState<TrafficEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [search, setSearch] = useState('');
  const [filterPrediction, setFilterPrediction] = useState<string>('ALL');

  const [interfaces, setInterfaces] = useState<NetworkInterfaceInfo[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string>('');
  const [captureStatus, setCaptureStatus] = useState<CaptureStatus | null>(parentCaptureStatus || null);
  const [switchingInterface, setSwitchingInterface] = useState(false);

  const loadCaptureState = async () => {
    try {
      const [ifaceRes, statusRes, historyRes] = await Promise.all([
        trafficApi.getInterfaces(),
        trafficApi.getCaptureStatus(),
        trafficApi.getHistory(50)
      ]);
      setInterfaces(ifaceRes.interfaces || []);
      setCaptureStatus(statusRes);
      if (onCaptureStatusChange) onCaptureStatusChange(statusRes);
      if (!selectedInterface && statusRes.active_interface) {
        setSelectedInterface(statusRes.active_interface);
      }
      setTrafficList(historyRes);
    } catch (e) {
      console.error('Failed to load live capture state', e);
    }
  };

  useEffect(() => {
    loadCaptureState();
    const interval = setInterval(async () => {
      try {
        const statusRes = await trafficApi.getCaptureStatus();
        setCaptureStatus(statusRes);
        if (onCaptureStatusChange) onCaptureStatusChange(statusRes);
      } catch {
        // ignore transient polling error
      }
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (latestEvent) {
      if (latestEvent.capture_status) {
        setCaptureStatus(latestEvent.capture_status);
        if (onCaptureStatusChange) onCaptureStatusChange(latestEvent.capture_status);
      }
      if (!isPaused) {
        setTrafficList((prev) => {
          const filtered = prev.filter((item) => item.id !== latestEvent.id);
          return [latestEvent, ...filtered].slice(0, 100);
        });
      }
    }
  }, [latestEvent, isPaused]);

  const handleInterfaceChange = async (newIface: string) => {
    setSelectedInterface(newIface);
    setSwitchingInterface(true);
    try {
      const updated = await trafficApi.configureCapture(newIface, 'restart');
      setCaptureStatus(updated);
      if (onCaptureStatusChange) onCaptureStatusChange(updated);
    } catch (e) {
      console.error('Failed to switch capture interface', e);
    } finally {
      setSwitchingInterface(false);
    }
  };

  const handleToggleCaptureEngine = async () => {
    setSwitchingInterface(true);
    try {
      const action = captureStatus?.is_running ? 'stop' : 'start';
      const updated = await trafficApi.configureCapture(selectedInterface || captureStatus?.active_interface, action);
      setCaptureStatus(updated);
      if (onCaptureStatusChange) onCaptureStatusChange(updated);
    } catch (e) {
      console.error('Failed to toggle capture engine', e);
    } finally {
      setSwitchingInterface(false);
    }
  };

  const filteredTraffic = trafficList.filter((item) => {
    const matchesSearch =
      item.source_ip.toLowerCase().includes(search.toLowerCase()) ||
      item.destination_ip.toLowerCase().includes(search.toLowerCase()) ||
      item.protocol.toLowerCase().includes(search.toLowerCase());

    const matchesPrediction = filterPrediction === 'ALL' || item.prediction === filterPrediction;

    return matchesSearch && matchesPrediction;
  });

  const exportToCSV = () => {
    const headers = [
      "ID", "Timestamp", "Interface", "Source IP", "Source Port",
      "Destination IP", "Destination Port", "Protocol", "Packets",
      "Bytes", "Duration(s)", "Prediction", "Attack Type", "Confidence", "Model Name"
    ];
    const rows = filteredTraffic.map(t => [
      t.id,
      t.timestamp,
      t.interface || t.feature_data?.interface || captureStatus?.active_interface || 'Wi-Fi',
      t.source_ip,
      t.source_port,
      t.destination_ip,
      t.destination_port,
      t.protocol,
      t.packet_count || t.feature_data?.packet_count || 1,
      t.packet_size,
      t.flow_duration ?? 0,
      t.prediction,
      t.attack_type,
      (t.confidence * 100).toFixed(1) + '%',
      t.model_name
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `AI_NIDS_Real_Traffic_Export_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Header Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-soc-border pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
              <Activity className="w-6 h-6 text-sky-400 animate-pulse" /> Real-Time Network Traffic Capture
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
              REAL MODE (PASSIVE SCAPY + NPCAP)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Passive live packet capture, 5-tuple flow aggregation, and NSL-KDD 20-feature ML classification
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={handleToggleCaptureEngine}
            disabled={switchingInterface}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all border ${
              captureStatus?.is_running
                ? 'bg-rose-500/15 text-rose-400 border-rose-500/40 hover:bg-rose-500/25'
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/30'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            {captureStatus?.is_running ? 'Stop Sniffer' : 'Start Sniffer'}
          </button>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all border ${
              isPaused
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 hover:bg-amber-500/30'
                : 'bg-slate-800 text-slate-300 border-soc-border hover:bg-slate-700'
            }`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
            {isPaused ? 'Resume Table' : 'Pause Table'}
          </button>

          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-sky-500/20"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>
      </div>

      {/* Permission / Error Alert Banner if Npcap or Permission error occurs */}
      {captureStatus?.last_error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 text-rose-300 text-xs font-mono flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-rose-400 mb-1">Packet Capture Diagnostic Warning</div>
            <div>{captureStatus.last_error}</div>
          </div>
        </div>
      )}

      {/* Real Capture Telemetry & Interface Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1: Network Interface Selector */}
        <div className="soc-card space-y-2 md:col-span-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono uppercase flex items-center gap-1.5">
              <Wifi className="w-3.5 h-3.5 text-sky-400" /> Network Capture Interface (Npcap)
            </span>
            <span className="text-[11px] font-mono text-emerald-400">
              {captureStatus?.permission_status || 'Checking Npcap...'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedInterface || captureStatus?.active_interface || ''}
              onChange={(e) => handleInterfaceChange(e.target.value)}
              disabled={switchingInterface}
              className="w-full bg-slate-900 border border-soc-border text-xs text-white font-mono rounded-lg px-3 py-2 focus:outline-none focus:border-sky-500"
            >
              {interfaces.map((iface) => (
                <option key={iface.network_name || iface.name} value={iface.name}>
                  [{iface.type}] {iface.name} — {iface.description} ({iface.ip})
                </option>
              ))}
            </select>
            <button
              onClick={loadCaptureState}
              title="Refresh Interfaces"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-soc-border text-slate-300"
            >
              <RefreshCw className={`w-4 h-4 ${switchingInterface ? 'animate-spin text-sky-400' : ''}`} />
            </button>
          </div>
          <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>Host IP: <strong className="text-slate-200">{captureStatus?.interface_ip || 'Auto'}</strong></span>
            <span>Npcap: <strong className={captureStatus?.npcap_available ? 'text-emerald-400' : 'text-rose-400'}>{captureStatus?.npcap_available ? 'Installed' : 'Missing'}</strong></span>
            <span>WebSocket: <strong className={isWsConnected ? 'text-emerald-400' : 'text-amber-400'}>{isWsConnected ? 'Connected' : 'Reconnecting'}</strong></span>
          </div>
        </div>

        {/* Card 2: Raw Packets Captured */}
        <div className="soc-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono uppercase">
            <span>Packets Captured</span>
            <Layers className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono my-1">
            {captureStatus?.packets_captured?.toLocaleString() || 0}
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Last packet: <span className="text-sky-400">{captureStatus?.last_packet_at || 'Waiting...'}</span>
          </div>
        </div>

        {/* Card 3: Flow Aggregation Stats */}
        <div className="soc-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono uppercase">
            <span>Aggregated Flows</span>
            <Cpu className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono my-1">
            {captureStatus?.flows_processed?.toLocaleString() || 0}
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Active 5-tuple flows: <strong className="text-slate-200">{captureStatus?.active_flows || 0}</strong>
          </div>
        </div>
      </div>

      {/* Interface Visibility Scope Notice */}
      <div className="px-4 py-2.5 rounded-xl bg-slate-900/80 border border-soc-border text-[11px] text-slate-400 flex items-center gap-2.5 font-mono">
        <Info className="w-4 h-4 text-sky-400 shrink-0" />
        <span>
          {captureStatus?.visibility_notice ||
            "Passive Capture Visibility Scope: Capturing on a local Wi-Fi or Ethernet interface observes traffic to/from this host plus broadcast/multicast frames. Unicast traffic between other separate devices on a switched network requires switch port mirroring (SPAN)."}
        </span>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-soc-card p-4 rounded-xl border border-soc-border">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search Source/Dest IP, Protocol..."
            className="w-full pl-10 pr-4 py-1.5 bg-slate-900 border border-soc-border rounded-lg text-xs text-white focus:outline-none focus:border-sky-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterPrediction}
            onChange={(e) => setFilterPrediction(e.target.value)}
            className="bg-slate-900 border border-soc-border text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-sky-500"
          >
            <option value="ALL">All Classified Flows</option>
            <option value="NORMAL">Normal Traffic Only</option>
            <option value="ATTACK">Attacks Only</option>
          </select>

          <span className="text-xs font-mono text-slate-400 ml-auto">
            Showing <strong className="text-sky-400">{filteredTraffic.length}</strong> real flows
          </span>
        </div>
      </div>

      {/* Real-time Traffic Table */}
      <div className="soc-card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-soc-border text-slate-400 font-mono uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Timestamp</th>
                <th className="py-3.5 px-4">Interface</th>
                <th className="py-3.5 px-4">Source IP:Port</th>
                <th className="py-3.5 px-4">Destination IP:Port</th>
                <th className="py-3.5 px-4">Protocol</th>
                <th className="py-3.5 px-4">Pkts / Bytes</th>
                <th className="py-3.5 px-4">Prediction</th>
                <th className="py-3.5 px-4">Attack Type</th>
                <th className="py-3.5 px-4">Pred. Confidence</th>
                <th className="py-3.5 px-4">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border/50 font-mono">
              {filteredTraffic.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-500">
                    Waiting for network packets on {captureStatus?.active_interface || 'active interface'}... Generate browser/network activity to observe flows.
                  </td>
                </tr>
              ) : (
                filteredTraffic.map((traffic, idx) => {
                  const isAttack = traffic.prediction === 'ATTACK';
                  const pktCount = traffic.packet_count || traffic.feature_data?.packet_count || 1;
                  const ifaceName = traffic.interface || traffic.feature_data?.interface || captureStatus?.active_interface || 'Wi-Fi';
                  const timeStr = traffic.timestamp.includes('T')
                    ? new Date(traffic.timestamp).toLocaleTimeString()
                    : traffic.timestamp;

                  return (
                    <tr
                      key={`${traffic.id}-${idx}`}
                      className={`transition-colors ${
                        isAttack ? 'bg-rose-500/5 hover:bg-rose-500/10' : 'hover:bg-slate-800/40'
                      }`}
                    >
                      <td className="py-3 px-4 text-slate-400">{timeStr}</td>
                      <td className="py-3 px-4 text-slate-300">{ifaceName}</td>
                      <td className="py-3 px-4 text-slate-200">{formatEndpoint(traffic.source_ip, traffic.source_port)}</td>
                      <td className="py-3 px-4 text-slate-200">{formatEndpoint(traffic.destination_ip, traffic.destination_port)}</td>
                      <td className="py-3 px-4 text-sky-400 font-bold">
                        {formatProtocolDisplay(traffic.protocol, traffic.source_port, traffic.destination_port)}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {pktCount} pkts / {traffic.packet_size} B
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                          isAttack ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        }`}>
                          {traffic.prediction}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-200">{traffic.attack_type}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {(traffic.confidence * 100).toFixed(1)}% <span className="text-[10px] text-slate-500">({traffic.prediction})</span>
                      </td>
                      <td className="py-3 px-4">
                        <SeverityBadge severity={traffic.severity || (isAttack ? 'HIGH' : 'NORMAL')} />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
