/**
 * React hook for WebSocket integration
 */

import { useEffect, useCallback, useRef } from 'react';
import { WebSocketClient } from '../api/websocket';
import useDashboardStore from '../store/dashboardStore.js';

export const useWebSocket = () => {
  const store = useDashboardStore();
  const reconnectTimeoutRef = useRef(null);
  const wsClientRef = useRef(null);

  // Initialize WebSocket client
  useEffect(() => {
    wsClientRef.current = new WebSocketClient();
  }, []);

  // Setup WebSocket event handlers
  const setupEventHandlers = useCallback(() => {
    if (!wsClientRef.current) return;

    // Connection events
    wsClientRef.current.on('connected', () => {
      store.setConnectionStatus('connected');
    });

    wsClientRef.current.on('disconnected', () => {
      store.setConnectionStatus('disconnected');
    });

    wsClientRef.current.on('error', (error) => {
      console.error('WebSocket error:', error);
      store.setConnectionStatus('error');
    });

    // Pipeline events
    wsClientRef.current.on('pipeline_started', store.handlePipelineStarted);
    wsClientRef.current.on('pipeline_completed', store.handlePipelineCompleted);
    wsClientRef.current.on('pipeline_stopped', store.handlePipelineStopped);
    wsClientRef.current.on('pipeline_error', store.handlePipelineStopped);

    // Stage events
    wsClientRef.current.on('stage_started', store.handleStageStarted);
    wsClientRef.current.on('stage_completed', store.handleStageCompleted);
    wsClientRef.current.on('stage_progress', store.handleStageProgress);

    // Data update events
    wsClientRef.current.on('region_update', store.handleRegionUpdate);
    wsClientRef.current.on('iteration_update', store.handleIterationUpdate);
    wsClientRef.current.on('map_update', store.handleMapUpdate);
    wsClientRef.current.on('metrics_update', (data) => store.updateMetrics(data));

    // Custom event: pipeline status
    wsClientRef.current.on('pipeline-status', (status) => {
      store.setPipelineStatus(status);
    });
  }, [store]);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    try {
      if (wsClientRef.current) {
        await wsClientRef.current.connect();
        setupEventHandlers();
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      store.setConnectionStatus('error');
    }
  }, [setupEventHandlers, store]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
    }
    store.setConnectionStatus('disconnected');
  }, [store]);

  // Start pipeline
  const startPipeline = useCallback((config) => {
    store.resetState();
    if (wsClientRef.current) {
      wsClientRef.current.startPipeline(config);
    }
  }, [store]);

  // Send custom message
  const sendMessage = useCallback((message) => {
    if (wsClientRef.current) {
      wsClientRef.current.send(message);
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect, disconnect]);

  return {
    status: wsClientRef.current?.status || 'disconnected',
    connectionStatus: store.connectionStatus,
    connect,
    disconnect,
    startPipeline,
    sendMessage,
    isConnected: wsClientRef.current?.status === 'connected'
  };
};

export default useWebSocket;