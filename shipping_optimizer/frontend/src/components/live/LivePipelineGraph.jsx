/**
 * Live Pipeline Graph Component
 * Shows real-time pipeline execution stages
 */

import React from 'react';
import { motion } from 'framer-motion';
import { usePipelineStatus } from '../../hooks/useApiData';
import useDashboardStore from '../../store/dashboardStore.js';

const StageNode = ({ stage, isActive, isCompleted, isNext, progress }) => {
  return (
    <motion.div
      className="flex flex-col items-center"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative">
        <motion.div
          className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl shadow-lg ${
            isActive
              ? 'bg-blue-500 text-white'
              : isCompleted
              ? 'bg-green-500 text-white'
              : isNext
              ? 'bg-gray-300 text-gray-600'
              : 'bg-gray-200 text-gray-400'
          }`}
          animate={
            isActive
              ? {
                  scale: [1, 1.1, 1],
                  boxShadow: [
                    '0 0 0 0 rgba(59, 130, 246, 0.5)',
                    '0 0 0 10px rgba(59, 130, 246, 0)',
                    '0 0 0 0 rgba(59, 130, 246, 0)'
                  ]
                }
              : {}
          }
          transition={{ duration: 1, repeat: isActive ? Infinity : 0 }}
        >
          {isCompleted ? '✓' : stage.name.charAt(0)}
        </motion.div>
        {isActive && progress > 0 && (
          <div className="absolute -bottom-2 left-0 right-0">
            <div className="w-full bg-gray-200 rounded-full h-1">
              <motion.div
                className="bg-blue-500 h-1 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        )}
      </div>
      <p className="mt-2 text-sm font-medium text-gray-700 text-center max-w-24">
        {stage.name}
      </p>
      {isActive && (
        <motion.p
          className="text-xs text-blue-500 mt-1"
          initial={{ opacity: 0 }}
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          Running...
        </motion.p>
      )}
    </motion.div>
  );
};

const ConnectingLine = ({ isActive, isCompleted }) => {
  return (
    <motion.div
      className="flex-1 h-1 mx-4 my-8"
      initial={{ width: 0 }}
      animate={{ width: '100%' }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div
        className={`h-full rounded-full ${
          isCompleted ? 'bg-green-500' : isActive ? 'bg-blue-500' : 'bg-gray-300'
        }`}
      />
    </motion.div>
  );
};

const LivePipelineGraph = () => {
  const { status, currentStage, stages, loading } = usePipelineStatus();
  const isLive = useDashboardStore((state) => state.isLive);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4, 5].map((i) => (
              <React.Fragment key={i}>
                <div className="w-16 h-16 bg-gray-200 rounded-full"></div>
                {i < 5 && <div className="flex-1 h-1 bg-gray-200 mx-4"></div>}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-xl font-bold text-gray-900">Pipeline Execution</h2>
        <div className="flex items-center space-x-2">
          <span className={`w-3 h-3 rounded-full ${
            status === 'running' ? 'bg-green-500' :
            status === 'completed' ? 'bg-blue-500' :
            'bg-gray-400'
          }`}></span>
          <span className="text-sm font-medium text-gray-700 capitalize">
            {status}
          </span>
          {isLive && (
            <motion.span
              className="flex items-center text-green-500 text-xs ml-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            >
              LIVE
            </motion.span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        {stages.map((stage, index) => {
          const isActive = stage.status === 'running' || stage.name === currentStage;
          const isCompleted = stage.status === 'completed';
          const isNext = !isActive && !isCompleted && index === stages.findIndex(s => s.status === 'running');

          return (
            <React.Fragment key={stage.id || index}>
              <StageNode
                stage={stage}
                isActive={isActive}
                isCompleted={isCompleted}
                isNext={isNext}
                progress={stage.progress || 0}
              />
              {index < stages.length - 1 && (
                <ConnectingLine
                  isActive={isActive}
                  isCompleted={isCompleted}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {status === 'running' && currentStage && (
        <motion.div
          className="mt-6 p-4 bg-blue-50 rounded-lg"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="text-sm text-blue-700">
            Currently executing: <span className="font-semibold">{currentStage}</span>
          </p>
        </motion.div>
      )}

      {status === 'completed' && (
        <motion.div
          className="mt-6 p-4 bg-green-50 rounded-lg"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="text-sm text-green-700 font-semibold">
            Pipeline completed successfully!
          </p>
        </motion.div>
      )}
    </div>
  );
};

export default LivePipelineGraph;