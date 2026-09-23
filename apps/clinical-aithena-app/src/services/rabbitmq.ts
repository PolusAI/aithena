'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * Real-time pipeline status updates via WebSocket.
 *
 * Instead of connecting directly to RabbitMQ (which requires port 15674
 * to be reachable from the browser), the frontend connects to a WebSocket
 * endpoint on the FastAPI backend (`/ws/status/{sessionId}`).  The backend
 * subscribes to RabbitMQ on behalf of the browser and relays messages.
 *
 * This means only the API port (8000) needs to be accessible.
 */

export interface StatusUpdate {
    status: string;
    message: string;
    timestamp: Date;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Derive a WebSocket URL from the REST API base URL.
 *
 * Examples:
 *   http://localhost:8000       → ws://localhost:8000
 *   https://example.com/api     → wss://example.com/api
 */
function wsBaseUrl(): string {
    let url = API_BASE_URL;
    // If the API URL is relative, resolve against window.location
    if (url.startsWith('/')) {
        const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        url = `${proto}//${window.location.host}${url}`;
    } else {
        url = url.replace(/^http/, 'ws');
    }
    // Strip trailing slash
    return url.replace(/\/$/, '');
}

class StatusService {
    private ws: WebSocket | null = null;
    private statusUpdateCallback: ((status: StatusUpdate) => void) | null = null;
    private connectionChangeCallback: ((isConnected: boolean) => void) | null = null;
    private sessionId: string | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    isConnected(): boolean {
        return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
    }

    onStatusUpdate(callback: (status: StatusUpdate) => void) {
        this.statusUpdateCallback = callback;
    }

    onConnectionChange(callback: (isConnected: boolean) => void) {
        this.connectionChangeCallback = callback;
    }

    /**
     * Set (or change) the session ID.
     * Opens a new WebSocket connection for this session.
     */
    setSessionId(sessionId: string) {
        console.log('[Status] Setting session ID:', sessionId);
        this.sessionId = sessionId;
        // (Re)connect for the new session
        this.connect();
    }

    getSessionId(): string | null {
        return this.sessionId;
    }

    connect(): void {
        if (!this.sessionId) {
            console.warn('[Status] Cannot connect without a session ID');
            return;
        }

        // Tear down any existing connection
        this.cleanup();

        const url = `${wsBaseUrl()}/ws/status/${this.sessionId}`;
        console.log('[Status] Connecting to:', url);

        try {
            this.ws = new WebSocket(url);
        } catch (err) {
            console.error('[Status] Failed to create WebSocket:', err);
            this.handleError();
            return;
        }

        this.ws.onopen = () => {
            console.log('[Status] WebSocket connected');
            this.reconnectAttempts = 0;
            this.connectionChangeCallback?.(true);
        };

        this.ws.onmessage = (event: MessageEvent) => {
            if (!this.statusUpdateCallback) return;
            try {
                const parsed = JSON.parse(event.data);
                this.statusUpdateCallback({
                    status: parsed.status || event.data,
                    message: parsed.message || event.data,
                    timestamp: new Date(),
                });
            } catch {
                this.statusUpdateCallback({
                    status: event.data,
                    message: event.data,
                    timestamp: new Date(),
                });
            }
        };

        this.ws.onclose = (event: CloseEvent) => {
            console.log('[Status] WebSocket closed:', event.code, event.reason);
            this.connectionChangeCallback?.(false);
            // Only reconnect on abnormal close
            if (event.code !== 1000) {
                this.handleError();
            }
        };

        this.ws.onerror = (event: Event) => {
            console.error('[Status] WebSocket error:', event);
            // onclose will fire after onerror
        };
    }

    private handleError() {
        this.reconnectAttempts++;
        if (this.reconnectAttempts <= this.maxReconnectAttempts) {
            const delay = Math.min(2000 * this.reconnectAttempts, 10000);
            console.log(
                `[Status] Reconnecting in ${delay}ms ` +
                `(attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
            );
            this.reconnectTimer = setTimeout(() => this.connect(), delay);
        } else {
            console.error('[Status] Max reconnection attempts reached');
        }
    }

    private cleanup() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            // Prevent onclose handler from firing during cleanup
            this.ws.onclose = null;
            this.ws.onerror = null;
            this.ws.onmessage = null;
            if (this.ws.readyState === WebSocket.OPEN ||
                this.ws.readyState === WebSocket.CONNECTING) {
                this.ws.close(1000, 'cleanup');
            }
            this.ws = null;
        }
        this.connectionChangeCallback?.(false);
    }

    disconnect(): void {
        this.cleanup();
    }
}

// Singleton instance
const statusService = new StatusService();

/**
 * React hook for real-time pipeline status updates.
 */
export function useRabbitMQ() {
    const [connected, setConnected] = useState(false);
    const [statusUpdates, setStatusUpdates] = useState<StatusUpdate[]>([]);

    useEffect(() => {
        let mounted = true;

        const statusCallback = (status: StatusUpdate) => {
            if (mounted) {
                console.log('[Status] Update:', status.status);
                setStatusUpdates(prev => [...prev, status]);
            }
        };

        const connectionCallback = (isConnected: boolean) => {
            if (mounted) {
                console.log('[Status] Connection:', isConnected);
                setConnected(isConnected);
            }
        };

        statusService.onStatusUpdate(statusCallback);
        statusService.onConnectionChange(connectionCallback);

        return () => {
            mounted = false;
        };
    }, []);

    const clearStatusUpdates = useCallback(() => {
        setStatusUpdates([]);
    }, []);

    // Stable reference so useEffects that depend on this don't re-fire.
    const setSessionId = useCallback((sessionId: string) => {
        statusService.setSessionId(sessionId);
    }, []);

    return {
        connected,
        statusUpdates,
        clearStatusUpdates,
        setSessionId,
    };
}

export default statusService;
