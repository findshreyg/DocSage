import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    theme: 'dark',
    language: 'en',
    autoSave: true,
    notifications: true,
    maxFileSize: 50,
    defaultView: 'chat',
    apiTimeout: 30,
    debugMode: false
  });
  const [serviceStatus, setServiceStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    const savedSettings = localStorage.getItem('docsage_settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    }
  };

  const saveSettings = () => {
    localStorage.setItem('docsage_settings', JSON.stringify(settings));
    alert('Settings saved successfully!');
  };

  const resetSettings = () => {
    const confirmReset = window.confirm('Are you sure you want to reset all settings to default?');
    if (confirmReset) {
      const defaultSettings = {
        theme: 'dark',
        language: 'en',
        autoSave: true,
        notifications: true,
        maxFileSize: 50,
        defaultView: 'chat',
        apiTimeout: 30,
        debugMode: false
      };
      setSettings(defaultSettings);
      localStorage.setItem('docsage_settings', JSON.stringify(defaultSettings));
      alert('Settings reset to default!');
    }
  };

  const checkServiceHealth = async () => {
    setLoading(true);
    const services = [
      { name: 'API Gateway', endpoint: '/' },
      { name: 'Auth Service', endpoint: '/auth/health' },
      { name: 'File Service', endpoint: '/file/health' },
      { name: 'Conversation Service', endpoint: '/conversation/health' },
      { name: 'LLM Service', endpoint: '/llm/health' }
    ];

    const statusResults = {};

    for (const service of services) {
      try {
        const response = await fetch(`http://localhost:8000${service.endpoint}`);
        statusResults[service.name] = {
          status: response.ok ? 'healthy' : 'unhealthy',
          statusCode: response.status
        };
      } catch (error) {
        statusResults[service.name] = {
          status: 'error',
          error: error.message,
          statusCode: 'N/A'
        };
      }
    }

    setServiceStatus(statusResults);
    setLoading(false);
  };

  const clearCache = () => {
    const confirmClear = window.confirm('This will clear all cached data including tokens. You will need to log in again. Continue?');
    if (confirmClear) {
      localStorage.clear();
      sessionStorage.clear();
      alert('Cache cleared successfully!');
      navigate('/');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#22c55e';
      case 'unhealthy': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

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
        <h1 style={{ display: 'inline', margin: 0 }}>Settings</h1>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1000px' }}>
        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '2rem' }}>
          <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem' }}>Application Settings</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ color: '#9ca3af', fontWeight: '600', fontSize: '0.9rem' }}>Theme:</label>
              <select
                value={settings.theme}
                onChange={(e) => setSettings(prev => ({ ...prev, theme: e.target.value }))}
                style={{
                  padding: '0.75rem',
                  border: '1px solid #444',
                  borderRadius: '6px',
                  background: '#1e293b',
                  color: 'white',
                  fontSize: '1rem'
                }}
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
                <option value="auto">Auto</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ color: '#9ca3af', fontWeight: '600', fontSize: '0.9rem' }}>Language:</label>
              <select
                value={settings.language}
                onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value }))}
                style={{
                  padding: '0.75rem',
                  border: '1px solid #444',
                  borderRadius: '6px',
                  background: '#1e293b',
                  color: 'white',
                  fontSize: '1rem'
                }}
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ color: '#9ca3af', fontWeight: '600', fontSize: '0.9rem' }}>Default View:</label>
              <select
                value={settings.defaultView}
                onChange={(e) => setSettings(prev => ({ ...prev, defaultView: e.target.value }))}
                style={{
                  padding: '0.75rem',
                  border: '1px solid #444',
                  borderRadius: '6px',
                  background: '#1e293b',
                  color: 'white',
                  fontSize: '1rem'
                }}
              >
                <option value="chat">Chat View</option>
                <option value="key-value">Key-Value View</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ color: '#9ca3af', fontWeight: '600', fontSize: '0.9rem' }}>Max File Size (MB):</label>
              <input
                type="number"
                min="1"
                max="100"
                value={settings.maxFileSize}
                onChange={(e) => setSettings(prev => ({ ...prev, maxFileSize: parseInt(e.target.value) }))}
                style={{
                  padding: '0.75rem',
                  border: '1px solid #444',
                  borderRadius: '6px',
                  background: '#1e293b',
                  color: 'white',
                  fontSize: '1rem'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="checkbox"
                checked={settings.autoSave}
                onChange={(e) => setSettings(prev => ({ ...prev, autoSave: e.target.checked }))}
                style={{ width: '1.2rem', height: '1.2rem', cursor: 'pointer' }}
              />
              <label style={{ color: '#9ca3af', fontWeight: '600', fontSize: '0.9rem', cursor: 'pointer' }}>
                Auto-save conversations
              </label>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => setSettings(prev => ({ ...prev, notifications: e.target.checked }))}
                style={{ width: '1.2rem', height: '1.2rem', cursor: 'pointer' }}
              />
              <label style={{ color: '#9ca3af', fontWeight: '600', fontSize: '0.9rem', cursor: 'pointer' }}>
                Enable notifications
              </label>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', paddingTop: '1rem', borderTop: '1px solid #444' }}>
            <button 
              onClick={saveSettings} 
              style={{
                padding: '0.75rem 1.5rem',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s ease'
              }}
            >
              Save Settings
            </button>
            <button 
              onClick={resetSettings} 
              style={{
                padding: '0.75rem 1.5rem',
                background: '#1e293b',
                color: 'white',
                border: '1px solid #444',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s ease'
              }}
            >
              Reset to Default
            </button>
          </div>
        </div>

        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '2rem' }}>
          <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem' }}>Data Management</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div style={{ padding: '1.5rem', background: '#1e293b', border: '1px solid #444', borderRadius: '6px' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>Cache Management</h3>
              <div style={{ marginBottom: '1rem' }}>
                <button 
                  onClick={clearCache}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Clear All Cache
                </button>
              </div>
              <p style={{ color: '#9ca3af', fontSize: '0.875rem', margin: 0, lineHeight: 1.4 }}>
                This will clear all stored data including login tokens and cached files.
              </p>
            </div>
          </div>
        </div>

        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '2rem' }}>
          <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.5rem' }}>Service Status</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div>
              <button
                onClick={checkServiceHealth}
                disabled={loading}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  opacity: loading ? 0.5 : 1
                }}
              >
                {loading ? 'Checking...' : 'Refresh Status'}
              </button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
              {Object.entries(serviceStatus).map(([serviceName, status]) => (
                <div key={serviceName} style={{ background: '#1e293b', border: '1px solid #444', borderRadius: '6px', padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: '600', color: 'white' }}>{serviceName}</span>
                    <span style={{ color: getStatusColor(status.status), fontWeight: '600', fontSize: '0.875rem' }}>
                      ● {status.status}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: '#9ca3af' }}>
                    <div>Status Code: {status.statusCode}</div>
                    {status.error && (
                      <div style={{ color: '#ef4444' }}>Error: {status.error}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}