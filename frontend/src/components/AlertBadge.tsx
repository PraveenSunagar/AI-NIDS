import React from 'react';

interface AlertBadgeProps {
  severity?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'NORMAL' | string;
  status?: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | string;
}

export const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const sevUpper = severity?.toUpperCase();

  const styles = {
    CRITICAL: 'bg-rose-500/20 text-rose-400 border-rose-500/50 animate-pulse',
    HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
    MEDIUM: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    LOW: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
    NORMAL: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  }[sevUpper] || 'bg-slate-800 text-slate-300 border-slate-700';

  return (
    <span className={`px-2.5 py-0.5 rounded-md text-xs font-mono font-semibold border ${styles}`}>
      {sevUpper}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statUpper = status?.toUpperCase();

  const styles = {
    OPEN: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    ACKNOWLEDGED: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    RESOLVED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  }[statUpper] || 'bg-slate-800 text-slate-300 border-slate-700';

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${styles}`}>
      {statUpper}
    </span>
  );
};
