/**
 * Sparkline Component - Simple line chart for data trends
 */

import React from 'react';
import { motion } from 'framer-motion';

export const Sparkline = ({ data = [], color = '#00d4ff', width = 100, height = 30, className = '' }) => {
  if (!data || data.length < 2) {
    return <div className={`inline-block ${className}`} style={{ width, height }} />;
  }

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <motion.svg
      width={width}
      height={height}
      className={className}
      initial={{ pathLength: 0 }}
      animate={{ pathLength: 1 }}
      transition={{ duration: 0.5 }}
    >
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </motion.svg>
  );
};