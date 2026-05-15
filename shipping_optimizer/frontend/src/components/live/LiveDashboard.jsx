/**
 * Live Dashboard Component
 * Main dashboard component that integrates all real-time features
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import LiveKPICards from './LiveKPICards';
import LivePipelineGraph from './LivePipelineGraph';
import LiveRegionalCards from './LiveRegionalCards';
import { useWebSocket } from '../../hooks/useWebSocket.js';
import { usePipelineStatus } from '../../hooks/useApiData';
import useDashboardStore from '../../store/dashboardStore';

const ControlButton = ({ onClick, disabled, children, variant = 'primary' }) => {
  const baseClasses = 'px-6 py-2 rounded-lg font-medium transition-colors';
  const variants = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-300',
    secondary: 'bg-gray-500 text-white hover:bg-gray-600 disabled:bg-gray-300',
    danger: 'bg-red-500 text-white hover:bg-red-600 disabled:bg-gray-300',
    success: 'bg-green-500 text-white hover:bg-green-600 disabled:bg-gray-300'
  };

  return (
    <motion.button
      className={`${baseClasses} ${variants[variant]}`}
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
    >
      {children}
    </motion.button>
  );
};

const LiveDashboard = () => {
  const { startPipeline, isConnected, connectionStatus } = useWebSocket();
  const { status } = usePipelineStatus();
  const [config, setConfig] = useState({
    max_iterations: 3,
    convergence_threshold: 0.95,
    optimization_type: 'hybrid'
  });
  const [useRealPipeline, setUseRealPipeline] = useState(true);
  const [pipelineData, setPipelineData] = useState(null);

  const handleStartPipeline = () => {
    // Clear previous data
    setPipelineData(null);

    // Start pipeline with real data flag
    startPipeline({
      ...config,
      data: { use_real_pipeline: useRealPipeline }
    });
  };

  // Listen for pipeline completion
  useEffect(() => {
    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'pipeline_completed') {
        setPipelineData(data.data || data.results);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                AI Shipping Control Center
              </h1>
              <p className="text-sm text-gray-500">
                Real-time optimization dashboard {useRealPipeline && '(Live Pipeline Data)'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Pipeline Type Toggle */}
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={useRealPipeline}
                  onChange={(e) => setUseRealPipeline(e.target.checked)}
                  className="rounded text-blue-500"
                />
                <span className="text-sm text-gray-600">Use Real Pipeline</span>
              </label>

              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <span className={`w-3 h-3 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-green-500' :
                  connectionStatus === 'connecting' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}></span>
                <span className="text-sm text-gray-600 capitalize">
                  {connectionStatus}
                </span>
              </div>

              {/* Control Buttons */}
              <ControlButton
                onClick={handleStartPipeline}
                disabled={status === 'running' || !isConnected}
                variant={status === 'running' ? 'secondary' : 'primary'}
              >
                {status === 'running' ? 'Running...' : 'Start Pipeline'}
              </ControlButton>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Pipeline Data Display */}
        {pipelineData && (
          <motion.div
            className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              Pipeline Execution Complete!
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Weekly Profit:</span>
                <span className="ml-2 font-semibold text-green-700">
                  ${pipelineData.weeklyProfit?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Coverage:</span>
                <span className="ml-2 font-semibold text-blue-700">
                  {pipelineData.coveragePercentage?.toFixed(1) || 'N/A'}%
                </span>
              </div>
              <div>
                <span className="text-gray-600">Services:</span>
                <span className="ml-2 font-semibold text-purple-700">
                  {pipelineData.totalServices?.toLocaleString() || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Status:</span>
                <span className="ml-2 font-semibold text-green-700">
                  {status || 'Complete'}
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* KPI Cards */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <LiveKPICards />
        </motion.div>

        {/* Pipeline Graph */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <LivePipelineGraph />
        </motion.div>

        {/* Regional Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <LiveRegionalCards />
        </motion.div>

        {/* Instructions */}
        {status === 'idle' && !pipelineData && (
          <motion.div
            className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-lg font-semibold text-blue-800 mb-2">
              Getting Started
            </h3>
            <p className="text-blue-700 mb-4">
              Click "Start Pipeline" to run the optimization and see real-time results.
            </p>
            {useRealPipeline && (
              <div className="text-sm text-blue-600">
                <p>✅ Real pipeline mode is enabled - the dashboard will use actual optimization results.</p>
                <p>✅ Pipeline data will be streamed from test_orchestrator.py execution.</p>
              </div>
            )}
          </motion.div>
        )}

        {/* Live Indicator */}
        {status === 'running' && (
          <motion.div
            className="fixed bottom-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <motion.div
              className="w-2 h-2 bg-white rounded-full"
              animate={{ scale: [1, 1.5, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
            <span className="text-sm font-medium">
              {useRealPipeline ? 'Running Real Pipeline' : 'Pipeline Running'}
            </span>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default LiveDashboard;