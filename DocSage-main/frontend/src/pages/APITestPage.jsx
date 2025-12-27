import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function APITestPage() {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState({});
  const [token, setToken] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const storedToken = localStorage.getItem('docsage_token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const makeRequest = async (endpoint, method = 'GET', body = null, requiresAuth = false) => {
    const testId = `${method}-${endpoint}`;
    setLoading(prev => ({ ...prev, [testId]: true }));

    try {
      const headers = {
        'Content-Type': 'application/json',
      };

      if (requiresAuth && token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const config = {
        method,
        headers,
      };

      if (body && method !== 'GET') {
        config.body = JSON.stringify(body);
      }

      const response = await fetch(`http://localhost:8000${endpoint}`, config);
      const data = await response.text();
      
      let parsedData;
      try {
        parsedData = JSON.parse(data);
      } catch {
        parsedData = data;
      }

      setResults(prev => ({
        ...prev,
        [testId]: {
          status: response.status,
          statusText: response.statusText,
          data: parsedData,
          success: response.ok
        }
      }));

    } catch (error) {
      setResults(prev => ({
        ...prev,
        [testId]: {
          status: 'ERROR',
          statusText: error.message,
          data: null,
          success: false
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [testId]: false }));
    }
  };

  const renderResult = (testId) => {
    const result = results[testId];
    const isLoading = loading[testId];

    if (isLoading) {
      return (
        <div style={{ 
          padding: '1rem', 
          background: 'rgba(59, 130, 246, 0.1)', 
          border: '1px solid rgba(59, 130, 246, 0.2)',
          borderRadius: '4px', 
          color: '#3b82f6' 
        }}>
          Loading...
        </div>
      );
    }

    if (!result) {
      return (
        <div style={{ 
          padding: '1rem', 
          background: 'rgba(107, 114, 128, 0.1)', 
          border: '1px solid rgba(107, 114, 128, 0.2)',
          borderRadius: '4px', 
          color: '#9ca3af' 
        }}>
          Not tested
        </div>
      );
    }

    return (
      <div style={{ 
        padding: '1rem', 
        borderRadius: '4px', 
        background: result.success ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
        border: result.success ? '1px solid rgba(34, 197, 94, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
        color: result.success ? '#22c55e' : '#ef4444'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
          Status: {result.status} {result.statusText}
        </div>
        <div style={{ maxHeight: '200px', overflow: 'auto' }}>
          <pre style={{ 
            margin: 0, 
            fontSize: '0.75rem', 
            lineHeight: 1.4,
            whiteSpace: 'pre-wrap', 
            wordBreak: 'break-word' 
          }}>
            {JSON.stringify(result.data, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  const testEndpoints = [
    { name: 'API Gateway Health', endpoint: '/', method: 'GET', auth: false },
    { name: 'Auth Service Health', endpoint: '/auth/health', method: 'GET', auth: false },
    { name: 'File Service Health', endpoint: '/file/health', method: 'GET', auth: false },
    { name: 'Conversation Service Health', endpoint: '/conversation/health', method: 'GET', auth: false },
    { name: 'LLM Service Health', endpoint: '/llm/health', method: 'GET', auth: false },
    { name: 'Get User', endpoint: '/auth/get-user', method: 'GET', auth: true },
    { name: 'List Files', endpoint: '/file/list-uploads', method: 'GET', auth: true },
  ];

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
        <h1 style={{ display: 'inline', margin: 0 }}>API Endpoint Tester</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '2rem', height: 'calc(100vh - 150px)' }}>
        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '1.5rem', overflowY: 'auto' }}>
          <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem' }}>Configuration</h2>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#9ca3af', fontWeight: '600', fontSize: '0.875rem' }}>
              Current Token:
            </label>
            <textarea
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Login to get token automatically"
              rows={3}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #444',
                borderRadius: '4px',
                background: '#1e293b',
                color: 'white',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                resize: 'vertical'
              }}
            />
          </div>
        </div>

        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '1.5rem', overflowY: 'auto' }}>
          <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem' }}>API Endpoints</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {testEndpoints.map((test, index) => {
              const testId = `${test.method}-${test.endpoint}`;
              return (
                <div key={index} style={{ background: '#1e293b', border: '1px solid #444', borderRadius: '6px', padding: '1rem' }}>
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontWeight: '600', color: 'white', marginBottom: '0.5rem' }}>{test.name}</div>
                    <div style={{ 
                      fontFamily: 'monospace', 
                      fontSize: '0.875rem', 
                      color: '#9ca3af',
                      background: '#202123',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      display: 'inline-block',
                      minWidth: '200px'
                    }}>
                      {test.method} {test.endpoint}
                    </div>
                    {test.auth && (
                      <div style={{ 
                        fontSize: '0.75rem', 
                        color: '#f59e0b',
                        background: 'rgba(245, 158, 11, 0.1)',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        display: 'inline-block',
                        marginLeft: '0.5rem'
                      }}>
                        🔒 Auth Required
                      </div>
                    )}
                  </div>
                  <div style={{ marginBottom: '1rem' }}>
                    <button
                      onClick={() => makeRequest(test.endpoint, test.method, null, test.auth)}
                      disabled={loading[testId] || (test.auth && !token)}
                      style={{
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        padding: '0.5rem 1rem',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontWeight: '600',
                        transition: 'all 0.2s ease',
                        opacity: (loading[testId] || (test.auth && !token)) ? 0.5 : 1
                      }}
                    >
                      {loading[testId] ? 'Testing...' : 'Test'}
                    </button>
                  </div>
                  {renderResult(testId)}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}