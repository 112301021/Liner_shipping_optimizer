/**
 * React hook for WebSocket connection management
 */

import { useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../api/apiClient.js';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectOnMount?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (type: string, data?: any) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    reconnectOnMount = false,
    onConnect,
    onDisconnect,
    onError
  } = options;

  const isConnectedRef = useRef(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(async () => {
    try {
      await apiClient.connectWebSocket();
      isConnectedRef.current = true;
      onConnect?.();
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error('WebSocket connection failed'));
    }
  }, [onConnect, onError]);

  const disconnect = useCallback(() => {
    apiClient.disconnectWebSocket();
    isConnectedRef.current = false;
    onDisconnect?.();
  }, [onDisconnect]);

  const send = useCallback((type: string, data?: any) => {
    apiClient.sendWebSocketMessage(type, data);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Setup event listeners
  useEffect(() => {
    apiClient.onWebSocketEvent('disconnected', () => {
      isConnectedRef.current = false;
      onDisconnect?.();
    });

    return () => {
      apiClient.offWebSocketEvent('disconnected');
    };
  }, [onDisconnect]);

  return {
    isConnected: isConnectedRef.current,
    connect,
    disconnect,
    send
  };
}

// ============================================================================
// Specialized WebSocket Hooks
// ============================================================================

export function usePipelineWebSocket() {
  const { isConnected, connect, disconnect, send } = useWebSocket({
    autoConnect: true,
    onConnect: () => console.log('Pipeline WebSocket connected'),
    onDisconnect: () => console.log('Pipeline WebSocket disconnected')
  });

  const startPipeline = useCallback((config?: any) => {
    send('start_pipeline', config);
  }, [send]);

  const stopPipeline = useCallback(() => {
    send('stop_pipeline');
  }, [send]);

  const ping = useCallback(() => {
    send('ping');
  }, [send]);

  return {
    isConnected,
    connect,
    disconnect,
    startPipeline,
    stopPipeline,
    ping
  };
}

export function useWebSocketEvent<T = any>(
  eventType: string,
  callback: (data: T) => void,
  deps: any[] = []
) {
  useEffect(() => {
    apiClient.onWebSocketEvent(eventType, callback);

    return () => {
      apiClient.offWebSocketEvent(eventType);
    };
  }, deps);
}