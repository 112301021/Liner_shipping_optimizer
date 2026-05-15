import React from 'react';

// Simple debug component with guaranteed visible styling
export default function DebugDashboard() {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: '#ff0000',
      color: '#ffffff',
      fontSize: '48px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 999999
    }}>
      DASHBOARD MOUNTS HERE
    </div>
  );
}