import React, { useState } from 'react';
import api from '../../services/api';

interface SetupFormProps {
  onSuccess: () => void;
}

export default function SetupForm({ onSuccess }: SetupFormProps) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await api.post('/api/v1/auth/setup', {
        full_name: fullName,
        email,
        password,
      });
      // On success, call the callback to trigger a re-render of the parent
      // which will then show the login form.
      onSuccess();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      if (Array.isArray(errorDetail) && errorDetail.length > 0) {
        // Display the message from the first validation error
        setError(errorDetail[0].msg || 'Setup failed. Please try again.');
      } else {
        setError(errorDetail || 'Setup failed. Please try again.');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Create Admin Account</h3>
      <p>Welcome! As the first user, you will be the administrator.</p>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div style={{ marginBottom: '15px' }}>
        <label>Full Name</label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
          style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
        />
      </div>
      <div style={{ marginBottom: '15px' }}>
        <label>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
        />
      </div>
      <div style={{ marginBottom: '15px' }}>
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
      </div>
      <button type="submit" style={{ width: '100%', padding: '10px', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
        Create Account
      </button>
    </form>
  );
}