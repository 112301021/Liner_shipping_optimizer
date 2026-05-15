/**
 * Counter Component - Animated number display
 */

import React from 'react';
import { motion } from 'framer-motion';

export const Counter = ({ value, prefix = '', suffix = '', className = '', ...props }) => {
  return (
    <motion.span
      className={className}
      initial={{ scale: 1.2, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {prefix}{value}{suffix}
    </motion.span>
  );
};