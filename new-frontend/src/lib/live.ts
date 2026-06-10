/**
 * Live data streaming for the dashboard.
 *
 * Provides a reactive data source that:
 * 1. Uses EventSource (SSE) when available for real-time updates
 * 2. Falls back to polling every 15 seconds if SSE is not supported
 * 3. Emits events that the dashboard can subscribe to
 *
 * This mirrors the old `/dump` SSE endpoint pattern.
 */

import { api, type HostData, type QueryResult, type VisitLogEntry } from './api';

export interface DumpPayload {
  sites: Record<string, {
    visits: {
      day: QueryResult;
      yesterday: QueryResult;
      all: QueryResult;
    };
    logs: VisitLogEntry[];
  }>;
  user: {
    uuid: string;
    prefs: {
      utcoffset: number;
    };
  };
  meta: {
    utcoffset: number;
  };
}

export type LiveEventType = 'dump' | 'archive' | 'nouser' | 'error' | 'connected' | 'disconnected';

export interface LiveEvent {
  type: LiveEventType;
  data: unknown;
}

type EventCallback = (event: LiveEvent) => void;

/**
 * Live data stream that connects to the backend SSE endpoint
 * or falls back to polling.
 */
export class LiveStream {
  private eventSource: EventSource | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private callbacks: Set<EventCallback> = new Set();
  private hosts: HostData[] = [];
  private hostNames: string[] = [];
  private utcoffset: number;
  private useSSE: boolean;
  private connected: boolean = false;

  constructor(utcoffset?: number) {
    this.utcoffset = utcoffset ?? this.getBrowserUtcOffset();
    this.useSSE = typeof EventSource !== 'undefined';
  }

  private getBrowserUtcOffset(): number {
    return Math.round((-1 * new Date().getTimezoneOffset()) / 60);
  }

  /**
   * Subscribe to live events.
   * Returns an unsubscribe function.
   */
  subscribe(callback: EventCallback): () => void {
    this.callbacks.add(callback);
    return () => {
      this.callbacks.delete(callback);
    };
  }

  private emit(type: LiveEventType, data: unknown): void {
    const event: LiveEvent = { type, data };
    for (const cb of this.callbacks) {
      try {
        cb(event);
      } catch (err) {
        console.error('LiveStream callback error:', err);
      }
    }
  }

  /**
   * Set the hosts the user has access to.
   * This is used for polling-based data fetching.
   */
  setHosts(hosts: HostData[]): void {
    this.hosts = hosts;
    this.hostNames = hosts.map(h => h.name);
  }

  /**
   * Start the live stream connection.
   */
  async start(): Promise<void> {
    if (this.connected) return;

    if (this.useSSE && !this.eventSource) {
      await this.connectSSE();
    }

    if (!this.eventSource) {
      this.startPolling();
    }
  }

  /**
   * Stop the live stream connection and clean up.
   */
  stop(): void {
    this.stopSSE();
    this.stopPolling();
    this.connected = false;
    this.emit('disconnected', null);
  }

  private stopSSE(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  /**
   * Connect to the backend SSE endpoint.
   * Falls back to polling silently if the connection fails.
   */
  private async connectSSE(): Promise<void> {
    try {
      const url = `/api/core/dump/?utcoffset=${this.utcoffset}`;
      this.eventSource = new EventSource(url);

      this.eventSource.addEventListener('dump', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as DumpPayload;
          this.connected = true;
          this.emit('connected', null);
          this.emit('dump', data);
        } catch (err) {
          console.error('Failed to parse dump event:', err);
        }
      });

      this.eventSource.addEventListener('archive', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          this.emit('archive', data);
        } catch {
          // ignore parse errors for archive
        }
      });

      this.eventSource.addEventListener('nouser', () => {
        this.emit('nouser', null);
        this.stop();
      });

      this.eventSource.onerror = () => {
        this.emit('error', { message: 'SSE connection error' });
        // Close and fall back to polling
        this.stopSSE();
        this.startPolling();
      };

      this.eventSource.onopen = () => {
        this.connected = true;
        this.emit('connected', null);
      };
    } catch (err) {
      console.error('Failed to create EventSource:', err);
      this.eventSource = null;
    }
  }

  /**
   * Fall back to polling when SSE is unavailable.
   */
  private startPolling(): void {
    if (this.pollTimer) return;

    const pollIntervalMs = 15000;

    // Do an immediate poll
    this.pollOnce();

    this.pollTimer = setInterval(() => {
      this.pollOnce();
    }, pollIntervalMs);
  }

  private async pollOnce(): Promise<void> {
    if (this.hostNames.length === 0) return;

    try {
      const now = new Date();
      const today = now.toISOString().slice(0, 10);
      const yesterday = new Date(now.getTime() - 86400000).toISOString().slice(0, 10);

      const sites: DumpPayload['sites'] = {};

      for (const hostName of this.hostNames) {
        const [dayData, yesterdayData, allData, logsResponse] = await Promise.all([
          api.query(hostName, today, today),
          api.query(hostName, yesterday, yesterday),
          api.query(hostName),
          api.getVisitLogs(hostName, 30),
        ]);

        sites[hostName] = {
          visits: {
            day: dayData ?? {},
            yesterday: yesterdayData ?? {},
            all: allData ?? {},
          },
          logs: logsResponse?.logs ?? [],
        };
      }

      const payload: DumpPayload = {
        sites,
        user: {
          uuid: '',
          prefs: { utcoffset: this.utcoffset },
        },
        meta: { utcoffset: this.utcoffset },
      };

      if (!this.connected) {
        this.connected = true;
        this.emit('connected', null);
      }
      this.emit('dump', payload);
    } catch (err) {
      if (this.connected) {
        this.connected = false;
        this.emit('disconnected', null);
      }
      this.emit('error', { message: err instanceof Error ? err.message : 'Poll failed' });
    }
  }

  /**
   * Whether the stream is currently connected.
   */
  isConnected(): boolean {
    return this.connected;
  }
}

/**
 * Create a singleton LiveStream instance.
 */
let globalLiveStream: LiveStream | null = null;

export function getLiveStream(utcoffset?: number): LiveStream {
  if (!globalLiveStream) {
    globalLiveStream = new LiveStream(utcoffset);
  }
  return globalLiveStream;
}
