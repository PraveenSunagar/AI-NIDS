import React, { useState, useEffect } from 'react';
import { User, TrafficEvent } from './types';
import { authApi } from './services/api';
import { TrafficWebSocketClient } from './services/websocket';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { LiveTraffic } from './pages/LiveTraffic';
import { Detection } from './pages/Detection';
import { Alerts } from './pages/Alerts';
import { TrafficLogs } from './pages/TrafficLogs';
import { MLModel } from './pages/MLModel';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [latestEvent, setLatestEvent] = useState<TrafficEvent | null>(null);
  const [isWsConnected, setIsWsConnected] = useState(false);

  // Check stored auth token on mount
  useEffect(() => {
    const token = localStorage.getItem('nids_token');
    if (token) {
      authApi.getMe()
        .then((user) => setCurrentUser(user))
        .catch(() => localStorage.removeItem('nids_token'))
        .finally(() => setLoadingAuth(false));
    } else {
      setLoadingAuth(false);
    }
  }, []);

  // Connect WebSocket stream
  useEffect(() => {
    const wsClient = new TrafficWebSocketClient();
    
    const unsubscribeStatus = wsClient.onStatusChange((connected) => {
      setIsWsConnected(connected);
    });

    const unsubscribeMessage = wsClient.onMessage((data) => {
      setLatestEvent(data);
    });

    wsClient.connect();

    return () => {
      unsubscribeStatus();
      unsubscribeMessage();
      wsClient.disconnect();
    };
  }, []);

  const handleLoginSuccess = (user: User, token: string) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    localStorage.removeItem('nids_token');
    setCurrentUser(null);
  };

  if (loadingAuth) {
    return (
      <div className="min-h-screen bg-soc-bg flex items-center justify-center text-sky-400 font-mono text-sm">
        Initializing Security Environment...
      </div>
    );
  }

  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex min-h-screen bg-soc-bg text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isWsConnected={isWsConnected}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header user={currentUser} onLogout={handleLogout} />

        <main className="flex-1 p-6 overflow-y-auto">
          {activeTab === 'dashboard' && <Dashboard latestEvent={latestEvent} />}
          {activeTab === 'live-traffic' && <LiveTraffic latestEvent={latestEvent} isWsConnected={isWsConnected} />}
          {activeTab === 'detection' && <Detection />}
          {activeTab === 'alerts' && <Alerts currentUser={currentUser} />}
          {activeTab === 'logs' && <TrafficLogs />}
          {activeTab === 'ml-model' && <MLModel />}
          {activeTab === 'analytics' && <Analytics />}
          {activeTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}

export default App;
