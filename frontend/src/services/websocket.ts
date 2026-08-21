import { TrafficEvent } from '../types';

export class TrafficWebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Array<(data: TrafficEvent) => void> = [];
  private statusListeners: Array<(connected: boolean) => void> = [];
  private reconnectInterval = 3000;
  private isManuallyClosed = false;

  constructor(private url: string = 'ws://localhost:8000/api/traffic/ws') {}

  public connect() {
    this.isManuallyClosed = false;
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.notifyStatus(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data: TrafficEvent = JSON.parse(event.data);
          this.listeners.forEach((cb) => cb(data));
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      };

      this.ws.onclose = () => {
        this.notifyStatus(false);
        if (!this.isManuallyClosed) {
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        this.notifyStatus(false);
      };
    } catch (err) {
      console.error('Failed to initiate WebSocket connection:', err);
      this.notifyStatus(false);
    }
  }

  public disconnect() {
    this.isManuallyClosed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  public onMessage(callback: (data: TrafficEvent) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback);
    };
  }

  public onStatusChange(callback: (connected: boolean) => void) {
    this.statusListeners.push(callback);
    return () => {
      this.statusListeners = this.statusListeners.filter((cb) => cb !== callback);
    };
  }

  private notifyStatus(connected: boolean) {
    this.statusListeners.forEach((cb) => cb(connected));
  }
}
