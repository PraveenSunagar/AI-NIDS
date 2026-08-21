import React, { useState, useEffect } from 'react';
import { TrafficEvent } from '../types';
import { SeverityBadge } from '../components/AlertBadge';
import { Activity, Play, Pause, Download, Search, Filter } from 'lucide-react';
import { trafficApi } from '../services/api';

interface LiveTrafficProps {
  latestEvent: TrafficEvent | null;
  isWsConnected: boolean;
}

export const LiveTraffic: React.FC<LiveTrafficProps> = ({ latestEvent, isWsConnected }) => {
  const [trafficList, setTrafficList] = useState<TrafficEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [search, setSearch] = useState('');
  const [filterPrediction, setFilterPrediction] = useState<string>('ALL');

  useEffect(() => {
    // Initial fetch of recent traffic history
    trafficApi.getHistory(50).then((data) => {
      setTrafficList(data);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    if (latestEvent && !isPaused) {
      setTrafficList((prev) => [latestEvent, ...prev.slice(0, 99)]);
    }
  }, [latestEvent, isPaused]);

  const filteredTraffic = trafficList.filter((item) => {
    const matchesSearch = 
      item.source_ip.includes(search) || 
      item.destination_ip.includes(search) || 
      item.protocol.toLowerCase().includes(search.toLowerCase());
    
    const matchesPrediction = filterPrediction === 'ALL' || item.prediction === filterPrediction;

    return matchesSearch && matchesPrediction;
  });

  const exportToCSV = () => {
    const headers = ["ID", "Timestamp", "Source IP", "Destination IP", "Protocol", "Prediction", "Attack Type", "Confidence", "Model Name"];
    const rows = filteredTraffic.map(t => [
      t.id,
      t.timestamp,
      t.source_ip,
      t.destination_ip,
      t.protocol,
      t.prediction,
      t.attack_type,
      (t.confidence * 100).toFixed(1) + '%',
      t.model_name
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `AI_NIDS_Traffic_Export_${new Date().toISOString()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Header Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-soc-border pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-sky-400 animate-pulse" /> Live Network Traffic Monitor
          </h1>
          <p className="text-xs text-slate-400">Continuous WebSocket packet feed and automated intrusion classification</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all border ${
              isPaused 
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/40 hover:bg-amber-500/30' 
                : 'bg-slate-800 text-slate-300 border-soc-border hover:bg-slate-700'
            }`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
            {isPaused ? 'Resume Feed' : 'Pause Feed'}
          </button>

          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-sky-500/20"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-soc-card p-4 rounded-xl border border-soc-border">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search IP, Protocol..."
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
            <option value="ALL">All Detections</option>
            <option value="NORMAL">Normal Traffic Only</option>
            <option value="ATTACK">Attacks Only</option>
          </select>

          <span className="text-xs font-mono text-slate-400 ml-auto">
            Showing <strong className="text-sky-400">{filteredTraffic.length}</strong> packets
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
                <th className="py-3.5 px-4">Source IP</th>
                <th className="py-3.5 px-4">Destination IP</th>
                <th className="py-3.5 px-4">Protocol</th>
                <th className="py-3.5 px-4">Prediction</th>
                <th className="py-3.5 px-4">Attack Type</th>
                <th className="py-3.5 px-4">Confidence</th>
                <th className="py-3.5 px-4">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border/50 font-mono">
              {filteredTraffic.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No traffic records matched the selected criteria.
                  </td>
                </tr>
              ) : (
                filteredTraffic.map((traffic, idx) => {
                  const isAttack = traffic.prediction === 'ATTACK';
                  return (
                    <tr
                      key={`${traffic.id}-${idx}`}
                      className={`transition-colors ${
                        isAttack ? 'bg-rose-500/5 hover:bg-rose-500/10' : 'hover:bg-slate-800/40'
                      }`}
                    >
                      <td className="py-3 px-4 text-slate-400">{traffic.timestamp}</td>
                      <td className="py-3 px-4 text-slate-200">{traffic.source_ip}:{traffic.source_port}</td>
                      <td className="py-3 px-4 text-slate-200">{traffic.destination_ip}:{traffic.destination_port}</td>
                      <td className="py-3 px-4 text-sky-400 font-bold">{traffic.protocol}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                          isAttack ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        }`}>
                          {traffic.prediction}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-200">{traffic.attack_type}</td>
                      <td className="py-3 px-4 text-slate-300">{(traffic.confidence * 100).toFixed(1)}%</td>
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
