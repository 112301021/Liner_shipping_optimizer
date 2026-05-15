/**
 * FunnelView Component - GA and MILP analytics
 */

import React from 'react';
import { motion } from 'framer-motion';

const FunnelView = () => {
  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-sm font-mono text-white/60 uppercase tracking-wider">
        Genetic Algorithm & MILP Analytics
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          className="p-4 rounded-lg"
          style={{
            background: 'rgba(2,12,24,0.8)',
            border: '1px solid rgba(0,212,255,0.2)'
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="text-sm font-mono text-white/80 mb-3">Genetic Algorithm</div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Population Size:</span>
              <span className="text-white/80 font-mono">100</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Generations:</span>
              <span className="text-white/80 font-mono">50</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Mutation Rate:</span>
              <span className="text-white/80 font-mono">0.1</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Crossover Rate:</span>
              <span className="text-white/80 font-mono">0.8</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Best Fitness:</span>
              <span className="text-green-400 font-mono">0.947</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="p-4 rounded-lg"
          style={{
            background: 'rgba(2,12,24,0.8)',
            border: '1px solid rgba(0,212,255,0.2)'
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="text-sm font-mono text-white/80 mb-3">MILP Solver</div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Variables:</span>
              <span className="text-white/80 font-mono">1,247</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Constraints:</span>
              <span className="text-white/80 font-mono">3,892</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Solver:</span>
              <span className="text-white/80 font-mono">CBC</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Solve Time:</span>
              <span className="text-white/80 font-mono">2.3s</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-white/40">Gap:</span>
              <span className="text-green-400 font-mono">0.1%</span>
            </div>
          </div>
        </motion.div>
      </div>

      <motion.div
        className="p-4 rounded-lg"
        style={{
          background: 'rgba(2,12,24,0.8)',
          border: '1px solid rgba(0,212,255,0.2)'
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="text-sm font-mono text-white/80 mb-3">Optimization Funnel</div>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-32 text-xs font-mono text-white/40 text-right">Initial Pool:</div>
            <div className="flex-1 h-6 bg-gray-700 rounded relative overflow-hidden">
              <div className="absolute inset-0 bg-blue-500" style={{ width: '100%' }} />
              <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-white">10,000</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 text-xs font-mono text-white/40 text-right">After GA:</div>
            <div className="flex-1 h-6 bg-gray-700 rounded relative overflow-hidden">
              <div className="absolute inset-0 bg-green-500" style={{ width: '60%' }} />
              <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-white">6,000</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 text-xs font-mono text-white/40 text-right">MILP Filter:</div>
            <div className="flex-1 h-6 bg-gray-700 rounded relative overflow-hidden">
              <div className="absolute inset-0 bg-yellow-500" style={{ width: '30%' }} />
              <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-white">3,000</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-32 text-xs font-mono text-white/40 text-right">Final Solution:</div>
            <div className="flex-1 h-6 bg-gray-700 rounded relative overflow-hidden">
              <div className="absolute inset-0 bg-red-500" style={{ width: '12%' }} />
              <span className="absolute inset-0 flex items-center justify-center text-xs font-mono text-white">1,200</span>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default FunnelView;