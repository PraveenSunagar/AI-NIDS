import React, { useState, useEffect } from 'react';
import { User, TrafficEvent, CaptureStatus } from './types';
import { authApi, trafficApi } from './services/api';
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
  const [captureStatus, setCaptureStatus] = useState<CaptureStatus | null>(null);

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

  // Poll capture status periodically for Header & Sidebar indicators
  useEffect(() => {
    const fetchStatus = () => {
      trafficApi.getCaptureStatus().then(setCaptureStatus).catch(() => {});
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  // Connect WebSocket stream
  useEffect(() => {
    const wsClient = new TrafficWebSocketClient();
    
    const unsubscribeStatus = wsClient.onStatusChange((connected) => {
      setIsWsConnected(connected);
    });

    const unsubscribeMessage = wsClient.onMessage((data) => {
      setLatestEvent(data);
      if (data.capture_status) {
        setCaptureStatus(data.capture_status);
      }
    });

    wsClient.connect();

    return () => {
      unsubscribeStatus();
      unsubscribeMessage();
      wsClient.disconnect();
    };
  }, []);

  const handleLoginSuccess = (user: User, _token: string) => {
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
        captureStatus={captureStatus}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          user={currentUser}
          onLogout={handleLogout}
          captureStatus={captureStatus}
        />

        <main className="flex-1 p-6 overflow-y-auto">
          {activeTab === 'dashboard' && <Dashboard latestEvent={latestEvent} />}
          {activeTab === 'live-traffic' && (
            <LiveTraffic
              latestEvent={latestEvent}
              isWsConnected={isWsConnected}
              captureStatus={captureStatus}
              onCaptureStatusChange={setCaptureStatus}
            />
          )}
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
