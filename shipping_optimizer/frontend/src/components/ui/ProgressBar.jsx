/**
 * ProgressBar Component - Animated progress bar
 */

import React from 'react';
import { motion } from 'framer-motion';

export const ProgressBar = ({ value = 0, max = 100, color = '#00d4ff', height = 8, className = '' }) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={`bg-gray-200 rounded-full overflow-hidden ${className}`} style={{ height }}>
      <motion.div
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );
};