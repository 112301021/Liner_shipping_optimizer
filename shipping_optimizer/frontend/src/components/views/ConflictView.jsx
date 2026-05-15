/**
 * ConflictView Component - Conflict resolution visualization
 */

import React from 'react';
import { motion } from 'framer-motion';

const ConflictView = () => {
  const conflicts = [
    {
      id: 1,
      type: 'Vessel Capacity',
      severity: 'high',
      description: 'Multiple services competing for same vessel',
      resolution: 'Reallocated vessel to higher profit service',
      status: 'resolved'
    },
    {
      id: 2,
      type: 'Port Congestion',
      severity: 'medium',
      description: 'Exceeding port capacity at Singapore',
      resolution: 'Adjusted schedule to avoid peak hours',
      status: 'resolved'
    },
    {
      id: 3,
      type: 'Demand Priority',
      severity: 'low',
      description: 'Low profit route blocking high demand corridor',
      resolution: 'Pending manual review',
      status: 'pending'
    }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'resolved': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'active': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-sm font-mono text-white/60 uppercase tracking-wider">
        Conflict Resolution Dashboard
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <motion.div
          className="p-4 rounded-lg text-center"
          style={{
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.2)'
          }}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <div className="text-2xl font-bold text-red-400 font-mono mb-1">1</div>
          <div className="text-xs text-white/60 font-mono">Active Conflicts</div>
        </motion.div>

        <motion.div
          className="p-4 rounded-lg text-center"
          style={{
            background: 'rgba(245,158,11,0.1)',
            border: '1px solid rgba(245,158,11,0.2)'
          }}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="text-2xl font-bold text-yellow-400 font-mono mb-1">1</div>
          <div className="text-xs text-white/60 font-mono">Pending Review</div>
        </motion.div>

        <motion.div
          className="p-4 rounded-lg text-center"
          style={{
            background: 'rgba(16,185,129,0.1)',
            border: '1px solid rgba(16,185,129,0.2)'
          }}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="text-2xl font-bold text-green-400 font-mono mb-1">2</div>
          <div className="text-xs text-white/60 font-mono">Resolved Today</div>
        </motion.div>
      </div>

      <div className="space-y-3">
        {conflicts.map((conflict, index) => (
          <motion.div
            key={conflict.id}
            className="p-4 rounded-lg"
            style={{
              background: 'rgba(2,12,24,0.8)',
              border: `1px solid ${getStatusColor(conflict.status)}33`
            }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: getSeverityColor(conflict.severity) }}
                  />
                  <span className="text-sm font-mono text-white/80">{conflict.type}</span>
                  <span
                    className="text-xs font-mono px-2 py-0.5 rounded"
                    style={{
                      background: `${getStatusColor(conflict.status)}20`,
                      color: getStatusColor(conflict.status)
                    }}
                  >
                    {conflict.status}
                  </span>
                </div>
                <div className="text-xs text-white/60 mb-2">{conflict.description}</div>
                <div className="text-xs text-white/40">
                  Resolution: {conflict.resolution}
                </div>
              </div>
              <button
                className="px-3 py-1 rounded text-xs font-mono transition-all"
                style={{
                  background: 'rgba(0,212,255,0.08)',
                  border: '1px solid rgba(0,212,255,0.2)',
                  color: 'rgba(0,212,255,0.8)'
                }}
              >
                {conflict.status === 'resolved' ? 'View' : 'Resolve'}
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(2,12,24,0.8)',
          border: '1px solid rgba(0,212,255,0.2)'
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <div className="text-sm font-mono text-white/80 mb-3">Resolution Strategy</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-2">
              <span className="text-lg">🤖</span>
            </div>
            <div className="text-xs font-mono text-white/60">Auto-Resolve</div>
            <div className="text-xs text-white/40 mt-1">68% of conflicts</div>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-2">
              <span className="text-lg">👥</span>
            </div>
            <div className="text-xs font-mono text-white/60">Manual Review</div>
            <div className="text-xs text-white/40 mt-1">24% of conflicts</div>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-2">
              <span className="text-lg">⚠️</span>
            </div>
            <div className="text-xs font-mono text-white/60">Escalate</div>
            <div className="text-xs text-white/40 mt-1">8% of conflicts</div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default ConflictView;