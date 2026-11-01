import React from 'react';
import { 
  LayoutDashboard, 
  Activity, 
  ShieldAlert, 
  Search, 
  FileText, 
  Cpu, 
  BarChart3, 
  Settings as SettingsIcon,
  ShieldCheck,
  Radio
} from 'lucide-react';
import { CaptureStatus } from '../types';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isWsConnected: boolean;
  captureStatus?: CaptureStatus | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, isWsConnected, captureStatus }) => {
  const isCapturing = captureStatus?.is_running ?? isWsConnected;
  const modeLabel = (captureStatus?.mode || 'REAL') === 'REAL' ? 'REAL' : 'DEMO';

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'live-traffic', label: 'Live Traffic', icon: Activity, badge: isCapturing ? modeLabel : undefined },
    { id: 'detection', label: 'Detection Test', icon: Search },
    { id: 'alerts', label: 'Alerts', icon: ShieldAlert },
    { id: 'logs', label: 'Traffic Logs', icon: FileText },
    { id: 'ml-model', label: 'ML Model', icon: Cpu },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-soc-bg border-r border-soc-border flex flex-col justify-between h-screen sticky top-0 z-30">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-soc-border flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <ShieldCheck className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-wide leading-tight">AI-NIDS</h1>
            <p className="text-xs text-slate-400 font-mono">SOC Defense System</p>
          </div>
        </div>

        {/* Live Stream & Mode Status Indicator */}
        <div className="mx-4 my-4 p-3 rounded-lg bg-slate-900/60 border border-soc-border space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-sky-400" /> Capture Mode
            </span>
            <span className={`px-2 py-0.5 rounded-full font-mono font-bold text-[10px] ${
              isCapturing
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse'
                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
            }`}>
              {isCapturing ? `${modeLabel} ACTIVE` : 'PAUSED'}
            </span>
          </div>
          {captureStatus?.active_interface && (
            <div className="text-[11px] font-mono text-slate-400 truncate border-t border-soc-border/60 pt-1.5">
              NIC: <span className="text-sky-400">{captureStatus.active_interface}</span> ({captureStatus.packets_captured} pkts)
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="px-3 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg font-medium text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500 text-slate-950 animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Dataset & Model Badge Footer */}
      <div className="p-4 border-t border-soc-border bg-slate-950/40 text-xs">
        <div className="flex justify-between items-center text-slate-400 mb-1">
          <span>Dataset</span>
          <span className="font-mono text-slate-200">NSL-KDD</span>
        </div>
        <div className="flex justify-between items-center text-slate-400">
          <span>Selected Features</span>
          <span className="font-mono text-sky-400 font-semibold">20 Key Features</span>
        </div>
      </div>
    </aside>
  );
};
