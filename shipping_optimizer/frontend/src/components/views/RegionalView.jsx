/**
 * RegionalView Component - Regional agents visualization
 */

import React from 'react';
import { motion } from 'framer-motion';
import { useDashboardStore } from '../../store/dashboardStore';

const RegionalView = () => {
  const regions = useDashboardStore((state) => state.regions || []);

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-sm font-mono text-white/60 uppercase tracking-wider">
        Regional Agents
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {regions.length > 0 ? regions.map((region, index) => (
          <motion.div
            key={region.id || index}
            className="p-4 rounded-lg"
            style={{
              background: 'rgba(2,12,24,0.8)',
              border: '1px solid rgba(0,212,255,0.2)'
            }}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="text-sm font-mono text-white/80 mb-2">{region.name || `Region ${index + 1}`}</div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-white/40">Services:</span>
                <span className="text-white/80 font-mono">{region.services || 0}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/40">Demand:</span>
                <span className="text-white/80 font-mono">{region.demand || 0} TEU</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-white/40">Profit:</span>
                <span className="text-green-400 font-mono">${(region.profit || 0).toLocaleString()}</span>
              </div>
            </div>
          </motion.div>
        )) : (
          <div className="col-span-full text-center text-white/40 py-8">
            No regional data available
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default RegionalView;