/**
 * FeedbackView Component - Feedback loop visualization
 */

import React from 'react';
import { motion } from 'framer-motion';

const FeedbackView = () => {
  const feedbackData = [
    { iteration: 1, profit: 1250000, coverage: 0.78, convergence: 0.12 },
    { iteration: 2, profit: 1380000, coverage: 0.82, convergence: 0.08 },
    { iteration: 3, profit: 1420000, coverage: 0.84, convergence: 0.05 },
    { iteration: 4, profit: 1450000, coverage: 0.85, convergence: 0.03 },
    { iteration: 5, profit: 1460000, coverage: 0.86, convergence: 0.01 },
  ];

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-sm font-mono text-white/60 uppercase tracking-wider">
        Feedback Loop Optimization
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          className="p-4 rounded-lg"
          style={{
            background: 'rgba(2,12,24,0.8)',
            border: '1px solid rgba(0,212,255,0.2)'
          }}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="text-sm font-mono text-white/80 mb-4">Iteration Progress</div>
          <div className="space-y-3">
            {feedbackData.map((data, index) => (
              <div key={data.iteration} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-white/40">Iteration {data.iteration}:</span>
                  <span className="text-green-400 font-mono">${(data.profit / 1000000).toFixed(2)}M</span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-blue-500 to-green-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${data.coverage * 100}%` }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="p-4 rounded-lg"
          style={{
            background: 'rgba(2,12,24,0.8)',
            border: '1px solid rgba(0,212,255,0.2)'
          }}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="text-sm font-mono text-white/80 mb-4">Convergence Metrics</div>
          <div className="space-y-3">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/40">Current Convergence:</span>
                <span className="text-green-400 font-mono">0.01</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-green-500"
                  initial={{ width: 0 }}
                  animate={{ width: '99%' }}
                  transition={{ delay: 0.8 }}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/40">Profit Improvement:</span>
                <span className="text-blue-400 font-mono">16.8%</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-blue-500"
                  initial={{ width: 0 }}
                  animate={{ width: '83.2%' }}
                  transition={{ delay: 0.9 }}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/40">Coverage Gain:</span>
                <span className="text-yellow-400 font-mono">8%</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-yellow-500"
                  initial={{ width: 0 }}
                  animate={{ width: '86%' }}
                  transition={{ delay: 1 }}
                />
              </div>
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
        transition={{ delay: 0.5 }}
      >
        <div className="text-sm font-mono text-white/80 mb-3">Feedback Flow</div>
        <div className="flex items-center justify-center space-x-4">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center mb-2">
              <span className="text-2xl">🎯</span>
            </div>
            <span className="text-xs font-mono text-white/60">Initial</span>
          </div>
          <div className="text-white/20">→</div>
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-2">
              <span className="text-2xl">⚙️</span>
            </div>
            <span className="text-xs font-mono text-white/60">Optimize</span>
          </div>
          <div className="text-white/20">→</div>
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-yellow-500/20 flex items-center justify-center mb-2">
              <span className="text-2xl">📊</span>
            </div>
            <span className="text-xs font-mono text-white/60">Evaluate</span>
          </div>
          <div className="text-white/20">→</div>
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-2">
              <span className="text-2xl">🔄</span>
            </div>
            <span className="text-xs font-mono text-white/60">Feedback</span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default FeedbackView;