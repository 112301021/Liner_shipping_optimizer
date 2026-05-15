/**
 * React hooks for API data fetching
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client.js';
import useDashboardStore from '../store/dashboardStore.js';

// Hook for fetching metrics
export const useMetrics = (autoRefresh = true) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const store = useDashboardStore();

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.getMetrics();
      store.setMetrics(data.metrics);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [store]);

  useEffect(() => {
    fetchMetrics();

    let interval = null;
    if (autoRefresh && store.autoRefresh) {
      interval = setInterval(fetchMetrics, store.refreshInterval * 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchMetrics, autoRefresh, store.autoRefresh, store.refreshInterval]);

  return {
    metrics: store.metrics,
    loading,
    error,
    refetch: fetchMetrics
  };
};

// Hook for fetching regions
export const useRegions = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const store = useDashboardStore();

  const fetchRegions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.getRegions();
      store.setRegions(data.regions);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [store]);

  useEffect(() => {
    fetchRegions();
  }, [fetchRegions]);

  return {
    regions: store.regions,
    selectedRegion: store.selectedRegion,
    setSelectedRegion: store.setSelectedRegion,
    loading,
    error,
    refetch: fetchRegions
  };
};

// Hook for fetching pipeline status
export const usePipelineStatus = (autoRefresh = true) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const store = useDashboardStore();

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.getPipelineStatus();
      store.setPipelineStatus(data.state.status);
      store.setCurrentIteration(data.state.current_iteration);
      store.setTotalIterations(data.state.total_iterations);
      store.setCurrentStage(data.state.current_stage);
      store.setStages(data.state.stages || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [store]);

  useEffect(() => {
    fetchStatus();

    let interval = null;
    if (autoRefresh && store.autoRefresh && store.pipelineStatus === 'running') {
      interval = setInterval(fetchStatus, 2000); // Refresh every 2 seconds when running
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchStatus, autoRefresh, store.autoRefresh, store.pipelineStatus]);

  return {
    status: store.pipelineStatus,
    currentIteration: store.currentIteration,
    totalIterations: store.totalIterations,
    currentStage: store.currentStage,
    stages: store.stages,
    loading,
    error,
    refetch: fetchStatus
  };
};

// Hook for fetching iterations
export const useIterations = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const store = useDashboardStore();

  const fetchIterations = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.getIterations();
      store.setIterations(data.iterations);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [store]);

  useEffect(() => {
    fetchIterations();
  }, [fetchIterations]);

  return {
    iterations: store.iterations,
    selectedIteration: store.selectedIteration,
    setSelectedIteration: store.setSelectedIteration,
    loading,
    error,
    refetch: fetchIterations
  };
};

// Hook for fetching conflicts
export const useConflicts = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const store = useDashboardStore();

  const fetchConflicts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.getConflicts();
      store.setConflicts(data.conflicts);
      store.conflictsResolved = data.resolved_conflicts || 0;
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [store]);

  useEffect(() => {
    fetchConflicts();
  }, [fetchConflicts]);

  const resolveConflict = useCallback(async (conflictId) => {
    store.resolveConflict(conflictId);
    await fetchConflicts();
  }, [store, fetchConflicts]);

  return {
    conflicts: store.conflicts,
    conflictsResolved: store.conflictsResolved,
    loading,
    error,
    refetch: fetchConflicts,
    resolveConflict
  };
};

// Hook for map data
export const useMapData = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const store = useDashboardStore();

  const fetchMapData = useCallback(async () => {
    try {
      setLoading(true);
      // Fetch corridors and routes from regions
      const data = await apiClient.getRegions();
      const corridors = [];
      const routes = [];

      data.regions.forEach(region => {
        // Create mock corridors based on regions
        if (region.hub_ports && region.hub_ports.length > 1) {
          corridors.push({
            id: `${region.id}_corridor`,
            origin: region.hub_ports[0],
            destination: region.hub_ports[1],
            teu: region.weekly_profit / 100,
            coverage: region.coverage_percent
          });
        }
      });

      store.setCorridors(corridors);
      store.setRoutes(routes);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [store]);

  useEffect(() => {
    fetchMapData();
  }, [fetchMapData]);

  return {
    corridors: store.corridors,
    routes: store.routes,
    ports: store.ports,
    loading,
    error,
    refetch: fetchMapData
  };
};

// Hook for health check
export const useHealthCheck = (interval = 30000) => {
  const [isHealthy, setIsHealthy] = useState(true);
  const [lastCheck, setLastCheck] = useState(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiClient.healthCheck();
        setIsHealthy(true);
        setLastCheck(new Date());
      } catch {
        setIsHealthy(false);
      }
    };

    checkHealth();
    const intervalId = setInterval(checkHealth, interval);

    return () => clearInterval(intervalId);
  }, [interval]);

  return { isHealthy, lastCheck };
};