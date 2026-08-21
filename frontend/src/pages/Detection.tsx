import React, { useState } from 'react';
import { detectionApi } from '../services/api';
import { DetectionRequestPayload, DetectionResult } from '../types';
import { Search, ShieldAlert, ShieldCheck, Cpu, Zap, RefreshCw } from 'lucide-react';
import { SeverityBadge } from '../components/AlertBadge';

export const Detection: React.FC = () => {
  const [formData, setFormData] = useState<DetectionRequestPayload>({
    duration: 0.0,
    protocol_type: 'tcp',
    service: 'http',
    flag: 'SF',
    src_bytes: 250,
    dst_bytes: 1200,
    logged_in: 1,
    count: 5,
    srv_count: 5,
    serror_rate: 0.0,
    same_srv_rate: 1.0,
    diff_srv_rate: 0.0,
    dst_host_count: 100,
    dst_host_srv_count: 250,
    dst_host_same_srv_rate: 1.0,
    dst_host_diff_srv_rate: 0.0,
    dst_host_same_src_port_rate: 0.1,
    dst_host_srv_diff_host_rate: 0.0,
    dst_host_serror_rate: 0.0,
    dst_host_srv_serror_rate: 0.0,
    model_name: 'best'
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DetectionResult | null>(null);

  const presets = {
    normal: {
      title: '🟢 Normal HTTP Traffic',
      data: {
        duration: 0.5, protocol_type: 'tcp', service: 'http', flag: 'SF',
        src_bytes: 320, dst_bytes: 2400, logged_in: 1, count: 4, srv_count: 4,
        serror_rate: 0.0, same_srv_rate: 1.0, diff_srv_rate: 0.0,
        dst_host_count: 150, dst_host_srv_count: 250, dst_host_same_srv_rate: 1.0,
        dst_host_diff_srv_rate: 0.0, dst_host_same_src_port_rate: 0.1,
        dst_host_srv_diff_host_rate: 0.0, dst_host_serror_rate: 0.0, dst_host_srv_serror_rate: 0.0
      }
    },
    dos: {
      title: '🔴 DoS Neptune SYN Flood',
      data: {
        duration: 0.0, protocol_type: 'tcp', service: 'private', flag: 'S0',
        src_bytes: 0, dst_bytes: 0, logged_in: 0, count: 350, srv_count: 250,
        serror_rate: 1.0, same_srv_rate: 0.05, diff_srv_rate: 0.95,
        dst_host_count: 255, dst_host_srv_count: 5, dst_host_same_srv_rate: 0.02,
        dst_host_diff_srv_rate: 0.98, dst_host_same_src_port_rate: 0.0,
        dst_host_srv_diff_host_rate: 0.0, dst_host_serror_rate: 1.0, dst_host_srv_serror_rate: 1.0
      }
    },
    probe: {
      title: '🟡 Port Sweep Probe',
      data: {
        duration: 0.1, protocol_type: 'tcp', service: 'other', flag: 'REJ',
        src_bytes: 0, dst_bytes: 0, logged_in: 0, count: 120, srv_count: 2,
        serror_rate: 0.0, same_srv_rate: 0.02, diff_srv_rate: 0.98,
        dst_host_count: 255, dst_host_srv_count: 2, dst_host_same_srv_rate: 0.01,
        dst_host_diff_srv_rate: 0.99, dst_host_same_src_port_rate: 0.8,
        dst_host_srv_diff_host_rate: 0.5, dst_host_serror_rate: 0.0, dst_host_srv_serror_rate: 0.0
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await detectionApi.predict(formData);
      setResult(res);
    } catch (e) {
      console.error('Detection test failed', e);
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (presetKey: keyof typeof presets) => {
    setFormData((prev) => ({
      ...prev,
      ...presets[presetKey].data
    }));
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="border-b border-soc-border pb-4">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
          <Search className="w-6 h-6 text-sky-400" /> Interactive Traffic Detection Test Bench
        </h1>
        <p className="text-xs text-slate-400">Manually input network traffic features to evaluate real-time ML model classification</p>
      </div>

      {/* Preset Quick Load Bar */}
      <div className="bg-soc-card p-4 rounded-xl border border-soc-border space-y-2">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">Quick Presets:</span>
        <div className="flex flex-wrap gap-2">
          {Object.entries(presets).map(([key, item]) => (
            <button
              key={key}
              type="button"
              onClick={() => applyPreset(key as keyof typeof presets)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-soc-border text-xs text-slate-200 font-mono transition-colors"
            >
              {item.title}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form Column */}
        <div className="lg:col-span-2 soc-card space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="text-sm font-bold text-white border-b border-soc-border pb-2 uppercase tracking-wider text-sky-400">
              Traffic Feature Parameters (20 Key NSL-KDD Features)
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Protocol Type</label>
                <select name="protocol_type" value={formData.protocol_type} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white">
                  <option value="tcp">tcp</option>
                  <option value="udp">udp</option>
                  <option value="icmp">icmp</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Service</label>
                <select name="service" value={formData.service} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white">
                  <option value="http">http</option>
                  <option value="private">private</option>
                  <option value="smtp">smtp</option>
                  <option value="ftp">ftp</option>
                  <option value="domain_u">domain_u</option>
                  <option value="eco_i">eco_i</option>
                  <option value="other">other</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Status Flag</label>
                <select name="flag" value={formData.flag} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white">
                  <option value="SF">SF (Normal)</option>
                  <option value="S0">S0 (SYN Error)</option>
                  <option value="REJ">REJ (Rejected)</option>
                  <option value="RSTR">RSTR</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Duration (s)</label>
                <input type="number" step="0.1" name="duration" value={formData.duration} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Source Bytes</label>
                <input type="number" name="src_bytes" value={formData.src_bytes} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Destination Bytes</label>
                <input type="number" name="dst_bytes" value={formData.dst_bytes} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Logged In (0/1)</label>
                <input type="number" name="logged_in" min="0" max="1" value={formData.logged_in} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Connection Count</label>
                <input type="number" name="count" value={formData.count} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Service Count</label>
                <input type="number" name="srv_count" value={formData.srv_count} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">SYN Error Rate (0.0 - 1.0)</label>
                <input type="number" step="0.01" name="serror_rate" value={formData.serror_rate} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Same Service Rate</label>
                <input type="number" step="0.01" name="same_srv_rate" value={formData.same_srv_rate} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Diff Service Rate</label>
                <input type="number" step="0.01" name="diff_srv_rate" value={formData.diff_srv_rate} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Dst Host Count</label>
                <input type="number" name="dst_host_count" value={formData.dst_host_count} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Dst Host Service Count</label>
                <input type="number" name="dst_host_srv_count" value={formData.dst_host_srv_count} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Dst Host Same Srv Rate</label>
                <input type="number" step="0.01" name="dst_host_same_srv_rate" value={formData.dst_host_same_srv_rate} onChange={handleInputChange} className="w-full bg-slate-900 border border-soc-border rounded px-2.5 py-1.5 text-white" />
              </div>
            </div>

            <div className="pt-3 border-t border-soc-border flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Target Model:</span>
                <select name="model_name" value={formData.model_name} onChange={handleInputChange} className="bg-slate-900 border border-soc-border rounded px-2 py-1 text-sky-400 font-mono">
                  <option value="best">Best Model (Auto)</option>
                  <option value="DecisionTree">Decision Tree</option>
                  <option value="RandomForest">Random Forest</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-lg transition-all shadow-md shadow-sky-500/20 flex items-center gap-2 disabled:opacity-50"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                {loading ? 'Executing ML Classification...' : 'Analyze Traffic Payload'}
              </button>
            </div>
          </form>
        </div>

        {/* Prediction Results Display Card */}
        <div className="soc-card space-y-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white border-b border-soc-border pb-2 uppercase tracking-wider text-slate-300">
              Classification Result Verdict
            </h3>

            {result ? (
              <div className="mt-4 space-y-4">
                {/* Warning Banner if Attack */}
                {result.prediction === 'ATTACK' ? (
                  <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 text-rose-400 space-y-2 soc-glow-red">
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <ShieldAlert className="w-5 h-5 animate-bounce" />
                      <span>⚠ Suspicious Network Intrusion Detected</span>
                    </div>
                    <p className="text-xs text-rose-300/80">
                      Malicious payload pattern identified. Automatic security alert generated in SOC database.
                    </p>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 space-y-2 soc-glow-green">
                    <div className="flex items-center gap-2 font-bold text-sm">
                      <ShieldCheck className="w-5 h-5" />
                      <span>Benign / Normal Traffic Verdict</span>
                    </div>
                    <p className="text-xs text-emerald-300/80">
                      Traffic flow conforms to normal network baseline profile. No threat actions required.
                    </p>
                  </div>
                )}

                {/* Metrics detail table */}
                <div className="bg-slate-900/80 rounded-xl p-4 border border-soc-border space-y-3 font-mono text-xs">
                  <div className="flex justify-between items-center border-b border-soc-border/60 pb-2">
                    <span className="text-slate-400">Prediction:</span>
                    <span className={`font-bold px-2 py-0.5 rounded ${
                      result.prediction === 'ATTACK' ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {result.prediction}
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-soc-border/60 pb-2">
                    <span className="text-slate-400">Attack Type:</span>
                    <span className="text-slate-200 font-semibold">{result.attack_type}</span>
                  </div>

                  <div className="flex justify-between items-center border-b border-soc-border/60 pb-2">
                    <span className="text-slate-400">Model Confidence:</span>
                    <span className="text-sky-400 font-bold">{(result.confidence * 100).toFixed(1)}%</span>
                  </div>

                  <div className="flex justify-between items-center border-b border-soc-border/60 pb-2">
                    <span className="text-slate-400">ML Classifier Used:</span>
                    <span className="text-slate-200">{result.model_name}</span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Timestamp:</span>
                    <span className="text-slate-400">{result.timestamp}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-xs text-center space-y-2">
                <Cpu className="w-10 h-10 text-slate-600 mb-2" />
                <p>Fill features or select a preset and click <strong className="text-slate-300">"Analyze Traffic Payload"</strong> to evaluate.</p>
              </div>
            )}
          </div>

          <div className="text-[11px] text-slate-500 text-center border-t border-soc-border pt-3 font-mono">
            Model powered by NSL-KDD supervised classification engine.
          </div>
        </div>
      </div>
    </div>
  );
};
