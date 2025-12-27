import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function FilesPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    const token = localStorage.getItem('docsage_token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/file/list-uploads', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch files');
      }

      const data = await response.json();
      setFiles(data.files || []);
    } catch (error) {
      console.error('Error fetching files:', error);
      alert('Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFile = async (file) => {
    const token = localStorage.getItem('docsage_token');

    try {
      const response = await fetch('http://localhost:8000/file/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ file_hash: file.hash })
      });

      if (!response.ok) {
        throw new Error('Failed to generate download link');
      }

      const data = await response.json();
      window.open(data.url, '_blank');
    } catch (error) {
      console.error('Error downloading file:', error);
      alert(`Download error: ${error.message}`);
    }
  };

  const handleDeleteFile = async (file) => {
    const confirmDelete = window.confirm(`Are you sure you want to delete "${file.filename}"?`);
    if (!confirmDelete) return;

    const token = localStorage.getItem('docsage_token');

    try {
      const response = await fetch('http://localhost:8000/file/delete-file', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ file_hash: file.hash })
      });

      if (!response.ok) {
        throw new Error('Failed to delete file');
      }

      alert('File deleted successfully');
      fetchFiles();
    } catch (error) {
      console.error('Error deleting file:', error);
      alert(`Delete error: ${error.message}`);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', background: '#1e293b', color: 'white', minHeight: '100vh' }}>
        <div>Loading files...</div>
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
        <h1 style={{ display: 'inline', margin: 0 }}>File Manager</h1>
      </div>

      {files.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: '#9ca3af' }}>
          <p>No files found</p>
          <p>Upload some documents from the dashboard to get started</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
          {files.map(file => (
            <div 
              key={file.hash} 
              style={{ 
                background: '#202123', 
                border: '1px solid #444', 
                borderRadius: '8px', 
                padding: '1.5rem' 
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                <div style={{ fontSize: '2rem' }}>
                  {file.filename.toLowerCase().endsWith('.pdf') ? '📄' : 
                   file.filename.toLowerCase().match(/\.(docx?|xlsx?|pptx?)$/i) ? '📝' : '📎'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem', wordBreak: 'break-word' }}>
                    {file.filename}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#9ca3af', fontFamily: 'monospace' }}>
                    {file.hash.substring(0, 12)}...
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  onClick={() => handleDownloadFile(file)}
                  style={{
                    padding: '0.5rem 1rem',
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '600'
                  }}
                >
                  Download
                </button>
                <button
                  onClick={() => navigate(`/details/${file.hash}`)}
                  style={{
                    padding: '0.5rem 1rem',
                    background: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '600'
                  }}
                >
                  View Details
                </button>
                <button
                  onClick={() => handleDeleteFile(file)}
                  style={{
                    padding: '0.5rem 1rem',
                    background: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '600'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}