/**
 * Live KPI Cards Component
 * Displays real-time metrics with animated updates
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useMetrics } from '../../hooks/useApiData';
import useDashboardStore from '../../store/dashboardStore.js';

const formatCurrency = (value) => {
  if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  } else if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  }
  return `$${value.toLocaleString()}`;
};

const formatNumber = (value) => {
  return value.toLocaleString();
};

const KPICard = ({ title, value, subtitle, icon, color, trend, live }) => {
  const [previousValue, setPreviousValue] = React.useState(value);
  const [isIncreasing, setIsIncreasing] = React.useState(false);

  React.useEffect(() => {
    if (value !== previousValue) {
      setIsIncreasing(value > previousValue);
      setPreviousValue(value);
    }
  }, [value, previousValue]);

  return (
    <motion.div
      className={`bg-white rounded-lg shadow-lg p-6 border-l-4 ${color}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <motion.p
            className={`text-2xl font-bold ${isIncreasing ? 'text-green-600' : 'text-gray-900'}`}
            key={value}
            initial={{ scale: 1.1 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            {value}
          </motion.p>
          <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-3xl mb-2">{icon}</span>
          {live && (
            <motion.div
              className="flex items-center text-green-500 text-xs"
              initial={{ opacity: 0 }}
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
              LIVE
            </motion.div>
          )}
        </div>
      </div>
      {trend && (
        <div className={`mt-4 flex items-center text-sm ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
          <span>{trend > 0 ? '↑' : '↓'}</span>
          <span className="ml-1">{Math.abs(trend)}%</span>
        </div>
      )}
    </motion.div>
  );
};

const LiveKPICards = () => {
  const { metrics, loading, error } = useMetrics();
  const isLive = useDashboardStore((state) => state.isLive);
  const lastUpdate = useDashboardStore((state) => state.lastUpdate);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Error loading metrics: {error}</p>
      </div>
    );
  }

  const kpis = [
    {
      title: 'Weekly Profit',
      value: formatCurrency(metrics.weeklyProfit),
      subtitle: 'Last week revenue',
      icon: '💰',
      color: 'border-green-500',
      trend: 5.2
    },
    {
      title: 'Annual Projection',
      value: formatCurrency(metrics.annualProfit),
      subtitle: 'Projected yearly profit',
      icon: '📈',
      color: 'border-blue-500',
      trend: 5.2
    },
    {
      title: 'Demand Coverage',
      value: `${metrics.coveragePercentage.toFixed(1)}%`,
      subtitle: 'TEU demand covered',
      icon: '🎯',
      color: 'border-purple-500',
      trend: -1.2
    },
    {
      title: 'Active Services',
      value: formatNumber(metrics.totalServices),
      subtitle: 'Services deployed',
      icon: '🚢',
      color: 'border-orange-500',
      trend: 2.8
    }
  ];

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-900">Performance Metrics</h2>
        {lastUpdate && (
          <p className="text-sm text-gray-500">
            Last updated: {new Date(lastUpdate).toLocaleTimeString()}
          </p>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpis.map((kpi, index) => (
          <KPICard
            key={index}
            {...kpi}
            live={isLive}
          />
        ))}
      </div>
    </div>
  );
};

export default LiveKPICards;