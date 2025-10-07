'use client';

import React, { useState, useEffect } from 'react';
import { StatusUpdate } from '@/lib/types';
import { Client, Frame, Message, StompHeaders } from '@stomp/stompjs';
import SecureLogger from '@/lib/logger';

// Create a client-side logger instance
const wsLogger = new SecureLogger('WebSocket-Client');

// Constants for RabbitMQ configuration
const DEFAULT_EXCHANGE = 'ask-aithena-exchange';

interface RabbitMQConfig {
    wsUrl: string;
    exchange: string;
}

async function getRabbitMQConfig(): Promise<RabbitMQConfig> {
    const res = await fetch('/api/config');
    const config = await res.json();
    const wsUrl = config.rabbitmqWsUrl;

    if (!wsUrl) {
        const error = 'RabbitMQ WS URL not found in runtime config';
        wsLogger.error(error);
        throw new Error(error);
    }

    wsLogger.debug('RabbitMQ config from runtime', { wsUrl: '[REDACTED]' });

    return {
        wsUrl,
        exchange: DEFAULT_EXCHANGE
    };
}

class RabbitMQService {
    private client: Client | null = null;
    private statusUpdateCallback: ((status: StatusUpdate) => void) | null = null;
    private connected = false;
    private subscription: any = null;
    private connectionChangeCallback: ((isConnected: boolean) => void) | null = null;
    private heartbeatInterval: any = null;
    private sessionId: string | null = null;
    private config: RabbitMQConfig | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;

    isConnected(): boolean {
        return this.connected && this.client?.connected || false;
    }

    onStatusUpdate(callback: (status: StatusUpdate) => void) {
        this.statusUpdateCallback = callback;
    }

    onConnectionChange(callback: (isConnected: boolean) => void) {
        this.connectionChangeCallback = callback;
    }

    setSessionId(sessionId: string) {
        wsLogger.debug('Setting session ID', { sessionId: '[REDACTED]' });
        this.sessionId = sessionId;
        // If already connected, resubscribe with new session ID
        if (this.connected && this.client?.connected) {
            this.subscribe();
        }
    }

    getSessionId(): string | null {
        return this.sessionId;
    }

    async connect(): Promise<void> {
        if (this.connected && this.client?.connected) {
            wsLogger.debug('Already connected to RabbitMQ');
            return;
        }

        // Get configuration from environment
        try {
            this.config = await getRabbitMQConfig();
            wsLogger.debug('Got RabbitMQ config', { exchange: this.config.exchange });
        } catch (error) {
            wsLogger.error('Failed to get RabbitMQ config', error);
            throw error;
        }

        return new Promise((resolve, reject) => {
            // Clean up existing resources
            this.cleanup();

            // Use the WebSocket URL directly from configuration
            if (!this.config) {
                reject(new Error('RabbitMQ configuration not initialized'));
                return;
            }
            
            // Build full WebSocket URL from relative path
            let wsUrl = this.config.wsUrl;
            
            // If it's a relative path, construct full URL
            if (wsUrl.startsWith('/')) {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host;
                wsUrl = `${protocol}//${host}${wsUrl}`;
            }
            
            wsLogger.debug('Connecting to STOMP WebSocket', { 
                originalUrl: this.config.wsUrl,
                fullUrl: wsUrl 
            });

            // Create a new STOMP client
            this.client = new Client({
                brokerURL: wsUrl,
                connectHeaders: {
                    login: 'guest',
                    passcode: 'guest',
                },
                debug: function (str: string) {
                    // Only log STOMP debug in development
                    if (process.env.NODE_ENV === 'development') {
                        wsLogger.debug('STOMP Debug', { message: str.substring(0, 100) });
                    }
                },
                reconnectDelay: 5000,
                heartbeatIncoming: 4000,
                heartbeatOutgoing: 4000
            });

            // Connection successful
            this.client.onConnect = (frame: Frame) => {
                wsLogger.info('Connected to STOMP broker');
                this.connected = true;
                this.reconnectAttempts = 0;
                if (this.connectionChangeCallback) {
                    this.connectionChangeCallback(true);
                }

                // Only subscribe if we have a session ID
                if (this.sessionId) {
                    this.subscribe();
                }

                resolve();
            };

            // Connection error
            this.client.onStompError = (frame: Frame) => {
                wsLogger.error('STOMP Error', undefined, { 
                    message: frame.headers.message || 'Unknown error' 
                });
                this.handleConnectionError(frame);
                reject(new Error(`STOMP error: ${frame.headers.message}`));
            };

            // WebSocket level error
            this.client.onWebSocketError = (event: Event) => {
                wsLogger.error('WebSocket Error', event);
                this.handleConnectionError();
            };

            // Start the connection
            try {
                this.client.activate();
            } catch (error) {
                wsLogger.error('Error activating STOMP client', error);
                this.handleConnectionError();
                reject(error);
            }
        });
    }

    private handleConnectionError(frame?: Frame) {
        this.connected = false;
        if (this.connectionChangeCallback) {
            this.connectionChangeCallback(false);
        }

        // Attempt to reconnect if within limits
        this.reconnectAttempts++;
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            wsLogger.info('Attempting reconnection', { 
                attempt: this.reconnectAttempts, 
                maxAttempts: this.maxReconnectAttempts 
            });
            setTimeout(() => this.connect(), 5000 * this.reconnectAttempts);
        } else {
            wsLogger.error('Max reconnection attempts reached');
        }
    }

    private cleanup() {
        // Clear any existing heartbeat
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }

        // Clean up any existing client
        if (this.client) {
            try {
                this.client.deactivate();
            } catch (e) {
                wsLogger.debug('Error deactivating existing client', e as Error);
            }
        }

        // Reset connection state
        this.connected = false;
        if (this.connectionChangeCallback) {
            this.connectionChangeCallback(false);
        }
    }

    disconnect(): void {
        this.cleanup();
    }

    private subscribe(): void {
        if (!this.client || !this.sessionId || !this.config) {
            wsLogger.error('Cannot subscribe: client not initialized or session ID not set or config missing');
            return;
        }

        // Unsubscribe from any existing subscription
        if (this.subscription) {
            try {
                this.subscription.unsubscribe();
            } catch (e) {
                wsLogger.error('Error unsubscribing', e);
            }
        }

        // Subscribe to messages for this specific session
        const routingKey = `session.${this.sessionId}`;
        const destination = `/exchange/${this.config.exchange}/${routingKey}`;

        wsLogger.debug('Subscribing to exchange', { exchange: this.config.exchange });

        this.subscription = this.client.subscribe(destination, (message: Message) => {
            wsLogger.debug('Received message', { length: message.body.length });
            if (this.statusUpdateCallback) {
                try {
                    // Try to parse as JSON first
                    const parsed = JSON.parse(message.body);
                    this.statusUpdateCallback({
                        status: parsed.status || message.body,
                        message: parsed.message || message.body,
                        timestamp: new Date()
                    });
                } catch (e) {
                    // If not JSON, treat the entire message as both status and message
                    this.statusUpdateCallback({
                        status: message.body,
                        message: message.body,
                        timestamp: new Date()
                    });
                }
            }
        });
    }
}

// Create a singleton instance
const rabbitmqService = new RabbitMQService();

// Export the hook
export function useRabbitMQ() {
    const [connected, setConnected] = useState(false);
    const [statusUpdates, setStatusUpdates] = useState<StatusUpdate[]>([]);

    useEffect(() => {
        let mounted = true;

        // Set up callbacks first
        const statusCallback = (status: StatusUpdate) => {
            if (mounted) {
                wsLogger.debug('Received status update', { status: status.status });
                setStatusUpdates((prev: StatusUpdate[]) => [...prev, status]);
            }
        };

        const connectionCallback = (isConnected: boolean) => {
            if (mounted) {
                wsLogger.debug('Connection status changed', { connected: isConnected });
                setConnected(isConnected);
            }
        };

        rabbitmqService.onStatusUpdate(statusCallback);
        rabbitmqService.onConnectionChange(connectionCallback);

        // Then connect
        rabbitmqService.connect().catch(error => {
            wsLogger.error('Failed to connect to RabbitMQ', error);
        });

        return () => {
            mounted = false;
            rabbitmqService.disconnect();
        };
    }, []);

    const clearStatusUpdates = () => {
        setStatusUpdates([]);
    };

    return {
        connected,
        statusUpdates,
        clearStatusUpdates,
        setSessionId: (sessionId: string) => rabbitmqService.setSessionId(sessionId)
    };
}

export default rabbitmqService;
