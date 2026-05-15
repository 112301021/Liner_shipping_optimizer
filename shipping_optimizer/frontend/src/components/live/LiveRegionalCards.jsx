/**
 * Live Regional Cards Component
 * Displays real-time regional optimization results
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useRegions } from '../../hooks/useApiData';
import useDashboardStore from '../../store/dashboardStore.js';

const formatCurrency = (value) => {
  if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  } else if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  }
  return `$${value.toLocaleString()}`;
};

const RegionalCard = ({ region, onSelect, isSelected }) => {
  const isCompleted = region.status === 'completed';
  const isRunning = region.status === 'running';

  return (
    <motion.div
      className={`bg-white rounded-lg shadow-lg p-6 cursor-pointer border-2 transition-all ${
        isSelected ? 'border-blue-500 shadow-xl' : 'border-transparent'
      } ${isRunning ? 'ring-2 ring-blue-300' : ''}`}
      onClick={() => onSelect(region.id)}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{region.name}</h3>
          <p className="text-sm text-gray-500">Region {region.id?.toUpperCase()}</p>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
          isCompleted
            ? 'bg-green-100 text-green-800'
            : isRunning
            ? 'bg-blue-100 text-blue-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          {region.status}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500">Weekly Profit</p>
          <motion.p
            className="text-lg font-semibold text-green-600"
            key={region.weekly_profit}
            initial={{ scale: 1.1 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            {formatCurrency(region.weekly_profit)}
          </motion.p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Coverage</p>
          <div className="flex items-center">
            <p className="text-lg font-semibold text-blue-600">
              {region.coverage_percent?.toFixed(1)}%
            </p>
            <div className="ml-2 w-full bg-gray-200 rounded-full h-2 max-w-16">
              <motion.div
                className="bg-blue-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${region.coverage_percent || 0}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500">Services</p>
          <p className="text-lg font-semibold text-purple-600">
            {region.services_selected || 0}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Margin</p>
          <p className="text-lg font-semibold text-orange-600">
            {region.profit_margin_pct?.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Hub Ports */}
      {region.hub_ports && region.hub_ports.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 mb-1">Hub Ports</p>
          <div className="flex flex-wrap gap-1">
            {region.hub_ports.map((port, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
              >
                {port}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Progress Bar (when running) */}
      {isRunning && (
        <motion.div
          className="mt-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-500">Optimization Progress</span>
            <span className="text-xs text-gray-500">Processing...</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-blue-500 h-2 rounded-full"
              animate={{ width: ['0%', '100%'] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
            />
          </div>
        </motion.div>
      )}

      {/* Uncovered TEU (if any) */}
      {region.uncovered_teu && region.uncovered_teu > 0 && (
        <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
          <p className="text-xs text-yellow-700">
            ⚠️ {region.uncovered_teu.toLocaleString()} TEU uncovered
          </p>
        </div>
      )}
    </motion.div>
  );
};

const LiveRegionalCards = () => {
  const { regions, setSelectedRegion, selectedRegion, loading, error } = useRegions();
  const isLive = useDashboardStore((state) => state.isLive);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              </div>
              <div>
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Error loading regions: {error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-900">Regional Results</h2>
        {isLive && (
          <motion.div
            className="flex items-center text-green-500 text-xs"
            initial={{ opacity: 0 }}
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
            LIVE UPDATES
          </motion.div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {regions.map((region) => (
          <RegionalCard
            key={region.id}
            region={region}
            onSelect={setSelectedRegion}
            isSelected={selectedRegion === region.id}
          />
        ))}
      </div>
    </div>
  );
};

export default LiveRegionalCards;