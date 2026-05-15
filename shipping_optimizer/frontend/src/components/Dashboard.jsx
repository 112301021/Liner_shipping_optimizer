/**
 * Dashboard Component with WebSocket Integration
 * This component wraps the maritime dashboard with real-time data
 */

import React from 'react';
import MaritimeDashboard from '../../maritime_dashboard.jsx';

export default function Dashboard() {
  // MaritimeDashboard handles its own WebSocket connections and state management
  return <MaritimeDashboard />;
}