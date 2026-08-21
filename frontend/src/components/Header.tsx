import React from 'react';
import { User } from '../types';
import { Shield, LogOut, User as UserIcon, Activity } from 'lucide-react';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
  selectedModel?: string;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout, selectedModel = "RandomForest" }) => {
  return (
    <header className="h-16 bg-soc-bg border-b border-soc-border px-6 flex items-center justify-between sticky top-0 z-20 backdrop-blur-md bg-opacity-90">
      {/* System Status & Model info */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>SYSTEM ONLINE</span>
        </div>

        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-300 text-xs font-mono">
          <Activity className="w-3.5 h-3.5 text-sky-400" />
          <span>Model: <strong className="text-white">{selectedModel}</strong></span>
        </div>
      </div>

      {/* User Actions */}
      <div className="flex items-center gap-4">
        {user ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-soc-border">
              <div className="w-7 h-7 rounded-full bg-sky-500/20 border border-sky-500/40 text-sky-400 flex items-center justify-center font-bold text-xs">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-slate-200">{user.name}</div>
                <div className="text-[10px] text-sky-400 font-mono leading-none">{user.role}</div>
              </div>
            </div>

            <button
              onClick={onLogout}
              title="Logout"
              className="p-2 rounded-lg bg-slate-800 hover:bg-rose-500/20 hover:text-rose-400 border border-soc-border hover:border-rose-500/30 text-slate-400 transition-all duration-150"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="text-xs text-slate-400 font-mono">Guest Session</div>
        )}
      </div>
    </header>
  );
};
