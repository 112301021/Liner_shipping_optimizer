/**
 * PipelineView Component - Optimization pipeline visualization
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useDashboardStore } from '../../store/dashboardStore';

const PipelineView = () => {
  const pipelineStatus = useDashboardStore((state) => state.pipelineStatus);

  const stages = [
    { name: 'Data Loading', status: 'complete' },
    { name: 'Regional Selection', status: 'complete' },
    { name: 'Service Generation', status: pipelineStatus === 'running' ? 'running' : 'complete' },
    { name: 'Vessel Assignment', status: pipelineStatus === 'running' ? 'pending' : 'complete' },
    { name: 'Profit Optimization', status: pipelineStatus === 'running' ? 'pending' : 'complete' }
  ];

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-sm font-mono text-white/60 uppercase tracking-wider">
        Optimization Pipeline
      </div>

      <div className="space-y-3">
        {stages.map((stage, index) => (
          <motion.div
            key={stage.name}
            className="flex items-center gap-4 p-3 rounded-lg"
            style={{
              background: 'rgba(2,12,24,0.8)',
              border: `1px solid rgba(0,212,255,0.2)`
            }}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="flex items-center gap-3 flex-1">
              <div
                className="w-3 h-3 rounded-full"
                style={{
                  backgroundColor: stage.status === 'complete' ? '#10b981' :
                                 stage.status === 'running' ? '#f59e0b' : '#6b7280'
                }}
              />
              <span className="text-sm font-mono text-white/80">{stage.name}</span>
            </div>
            <span className="text-xs font-mono text-white/40">
              {stage.status === 'complete' ? '✓' :
               stage.status === 'running' ? '⏳' : '⏸'}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default PipelineView;