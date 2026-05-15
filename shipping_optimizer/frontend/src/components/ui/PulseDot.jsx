/**
 * PulseDot Component - Animated status indicator
 */

import React from 'react';
import { motion } from 'framer-motion';

export const PulseDot = ({ color = '#10b981', size = 8, className = '' }) => {
  return (
    <motion.div
      className={`rounded-full ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: color,
        boxShadow: `0 0 10px ${color}`
      }}
      animate={{
        scale: [1, 1.2, 1],
        opacity: [1, 0.7, 1]
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    />
  );
};