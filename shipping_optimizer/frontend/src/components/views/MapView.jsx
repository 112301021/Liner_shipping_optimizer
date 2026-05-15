/**
 * MapView Component - Maritime map visualization
 */

import React from 'react';
import { motion } from 'framer-motion';

const MapView = () => {
  return (
    <motion.div
      className="rounded-lg border"
      style={{
        background: 'rgba(2,12,24,0.8)',
        borderColor: 'rgba(0,212,255,0.2)',
        borderWidth: '1px',
        height: '400px'
      }}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="p-4 h-full flex items-center justify-center">
        <div className="text-center text-white/60">
          <div className="text-4xl mb-2">🗺️</div>
          <div className="text-sm font-mono">Maritime Map View</div>
          <div className="text-xs text-white/40 mt-2">Shipping corridors and vessel routes</div>
        </div>
      </div>
    </motion.div>
  );
};

export default MapView;