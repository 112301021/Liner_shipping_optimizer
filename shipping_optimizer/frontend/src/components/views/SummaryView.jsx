/**
 * SummaryView Component - Executive summary
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useDashboardStore } from '../../store/dashboardStore';

const SummaryView = () => {
  const metrics = useDashboardStore((state) => state.metrics);
  const runtime = useDashboardStore((state) => state.runtime);

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-sm font-mono text-white/60 uppercase tracking-wider">
        Executive Summary
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          className="p-6 rounded-lg"
          style={{
            background: 'rgba(2,12,24,0.8)',
            border: '1px solid rgba(0,212,255,0.2)'
          }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="text-lg font-mono text-white/80 mb-4">Performance Overview</div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Weekly Revenue</span>
              <span className="text-lg font-mono text-green-400">${metrics?.weeklyProfit?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Annual Projection</span>
              <span className="text-lg font-mono text-blue-400">${metrics?.annualProfit?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Demand Coverage</span>
              <span className="text-lg font-mono text-yellow-400">{metrics?.coveragePercentage?.toFixed(1) || '0'}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Profit Margin</span>
              <span className="text-lg font-mono text-purple-400">{metrics?.profitMargin?.toFixed(1) || '0'}%</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="p-6 rounded-lg"
          style={{
            background: 'rgba(2,12,24,0.8)',
            border: '1px solid rgba(0,212,255,0.2)'
          }}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="text-lg font-mono text-white/80 mb-4">Operational Metrics</div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Services Deployed</span>
              <span className="text-lg font-mono text-cyan-400">{metrics?.totalServices?.toLocaleString() || '0'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Active Regions</span>
              <span className="text-lg font-mono text-indigo-400">{metrics?.regions || '0'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Optimization Time</span>
              <span className="text-lg font-mono text-orange-400">{runtime}s</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-white/40">Convergence Score</span>
              <span className="text-lg font-mono text-pink-400">{metrics?.convergenceScore?.toFixed(3) || '0.000'}</span>
            </div>
          </div>
        </motion.div>
      </div>

      <motion.div
        className="p-6 rounded-lg"
        style={{
          background: 'rgba(2,12,24,0.8)',
          border: '1px solid rgba(0,212,255,0.2)'
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="text-lg font-mono text-white/80 mb-4">Key Insights</div>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-xs">✓</span>
            </div>
            <div>
              <div className="text-sm font-mono text-white/60">Profit Optimization</div>
              <div className="text-xs text-white/40">Successfully maximized weekly revenue with optimal vessel allocation</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-xs">✓</span>
            </div>
            <div>
              <div className="text-sm font-mono text-white/60">Demand Coverage</div>
              <div className="text-xs text-white/40">Achieved {metrics?.coveragePercentage?.toFixed(1) || '0'}% coverage with strategic routing</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-xs">!</span>
            </div>
            <div>
              <div className="text-sm font-mono text-white/60">Capacity Utilization</div>
              <div className="text-xs text-white/40">Consider increasing vessel capacity in high-demand corridors</div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-xs">→</span>
            </div>
            <div>
              <div className="text-sm font-mono text-white/60">Next Steps</div>
              <div className="text-xs text-white/40">Review seasonal demand patterns for next optimization cycle</div>
            </div>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="p-6 rounded-lg"
        style={{
          background: 'rgba(2,12,24,0.8)',
          border: '1px solid rgba(0,212,255,0.2)'
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <div className="text-lg font-mono text-white/80 mb-4">Recommendations</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 rounded" style={{ background: 'rgba(0,212,255,0.05)' }}>
            <div className="text-sm font-mono text-cyan-400 mb-1">Short Term</div>
            <ul className="text-xs text-white/40 space-y-1">
              <li>• Optimize vessel schedules for peak demand</li>
              <li>• Increase frequency on high-profit routes</li>
              <li>• Review pricing strategy for low-margin services</li>
            </ul>
          </div>
          <div className="p-3 rounded" style={{ background: 'rgba(0,212,255,0.05)' }}>
            <div className="text-sm font-mono text-cyan-400 mb-1">Long Term</div>
            <ul className="text-xs text-white/40 space-y-1">
              <li>• Consider fleet expansion for emerging markets</li>
              <li>• Invest in port infrastructure improvements</li>
              <li>• Develop AI-powered demand forecasting</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SummaryView;