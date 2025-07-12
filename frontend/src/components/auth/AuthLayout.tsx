import React from 'react';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' }}>
      <div style={{ padding: '40px', background: 'white', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', width: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <h2>PMS Tracker</h2>
        </div>
        {children}
      </div>
    </div>
  );
}