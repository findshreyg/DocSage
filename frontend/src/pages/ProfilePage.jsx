import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    const token = localStorage.getItem('docsage_token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/auth/get-user', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user data');
      }

      const userData = await response.json();
      setUser(userData);
    } catch (error) {
      console.error('Error fetching user data:', error);
      localStorage.removeItem('docsage_token');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('docsage_token');
    try {
      await fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      localStorage.removeItem('docsage_token');
      navigate('/');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', background: '#1e293b', color: 'white', minHeight: '100vh' }}>
        <div>Loading user profile...</div>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', background: '#1e293b', color: 'white', minHeight: '100vh' }}>
      <div style={{ marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid #444' }}>
        <button 
          onClick={() => navigate('/dashboard')} 
          style={{ 
            background: '#202123', 
            border: '1px solid #444', 
            color: 'white', 
            padding: '0.5rem 1rem', 
            borderRadius: '6px', 
            cursor: 'pointer',
            marginRight: '1rem'
          }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{ display: 'inline', margin: 0 }}>User Profile</h1>
      </div>

      <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '2rem', marginBottom: '2rem' }}>
        <h2 style={{ margin: '0 0 1rem 0' }}>Account Information</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: '#1e293b', border: '1px solid #444', borderRadius: '6px' }}>
            <span style={{ fontWeight: '600', color: '#9ca3af' }}>Name:</span>
            <span style={{ fontFamily: 'monospace' }}>{user?.name}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: '#1e293b', border: '1px solid #444', borderRadius: '6px' }}>
            <span style={{ fontWeight: '600', color: '#9ca3af' }}>Email:</span>
            <span style={{ fontFamily: 'monospace' }}>{user?.email}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: '#1e293b', border: '1px solid #444', borderRadius: '6px' }}>
            <span style={{ fontWeight: '600', color: '#9ca3af' }}>User ID:</span>
            <span style={{ fontFamily: 'monospace' }}>{user?.id}</span>
          </div>
        </div>
      </div>

      <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '2rem' }}>
        <h2 style={{ margin: '0 0 1rem 0' }}>Actions</h2>
        <button 
          onClick={handleLogout}
          style={{
            background: '#dc3545',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
}