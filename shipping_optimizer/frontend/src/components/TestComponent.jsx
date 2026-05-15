/**
 * Test Component
 * Simple component to verify React is rendering
 */

import React from 'react';

const TestComponent = () => {
  return (
    <div style={{ padding: '20px', backgroundColor: '#e0f2fe', border: '1px solid #0ea5e9', borderRadius: '8px', margin: '20px' }}>
      <h1 style={{ color: '#0c4a6e', marginBottom: '10px' }}>✅ React is Working!</h1>
      <p style={{ color: '#0e7490' }}>Current time: {new Date().toLocaleString()}</p>
      <p style={{ color: '#0e7490' }}>Component mounted successfully</p>
    </div>
  );
};

export default TestComponent;