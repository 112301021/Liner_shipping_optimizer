/**
 * KpiCard Component - Key Performance Indicator card with sparkline
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Counter, Sparkline } from './index';

export const KpiCard = ({
  label,
  value,
  sub,
  color = '#00d4ff',
  sparkData = [],
  trend = null,
  className = ''
}) => {
  return (
    <motion.div
      className={`rounded-lg border ${className}`}
      style={{
        background: 'rgba(2,12,24,0.8)',
        borderColor: `${color}33`,
        borderWidth: '1px'
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, borderColor: `${color}66` }}
      transition={{ duration: 0.3 }}
    >
      <div className="p-4">
        <div className="text-xs font-mono text-white/60 uppercase tracking-wider mb-2">
          {label}
        </div>

        <div className="flex items-baseline justify-between mb-2">
          <Counter
            value={value}
            className="text-2xl font-bold font-mono"
            style={{ color }}
          />
          {trend !== null && (
            <span
              className={`text-xs font-mono ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}
            >
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </span>
          )}
        </div>

        {sub && (
          <div className="text-xs font-mono text-white/40 mb-3">
            {sub}
          </div>
        )}

        {sparkData && sparkData.length > 0 && (
          <Sparkline
            data={sparkData}
            color={color}
            width="100%"
            height={40}
          />
        )}
      </div>
    </motion.div>
  );
};