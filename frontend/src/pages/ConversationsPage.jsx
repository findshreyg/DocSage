import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ConversationsPage() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [conversations, setConversations] = useState([]);
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

  const fetchConversations = async (fileHash) => {
    const token = localStorage.getItem('docsage_token');

    try {
      const response = await fetch(`http://localhost:8000/conversation/get-file-conversations?file_hash=${fileHash}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch conversations');
      }

      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setConversations([]);
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    fetchConversations(file.hash);
  };

  const handleDeleteConversation = async (question) => {
    if (!selectedFile) return;

    const confirmDelete = window.confirm(`Are you sure you want to delete the conversation for: "${question}"?`);
    if (!confirmDelete) return;

    const token = localStorage.getItem('docsage_token');

    try {
      const response = await fetch('http://localhost:8000/conversation/delete-conversation', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          file_hash: selectedFile.hash,
          question: question
        })
      });

      if (!response.ok) {
        throw new Error('Failed to delete conversation');
      }

      alert('Conversation deleted successfully');
      fetchConversations(selectedFile.hash);
    } catch (error) {
      console.error('Error deleting conversation:', error);
      alert('Failed to delete conversation');
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
        <h1 style={{ display: 'inline', margin: 0 }}>Conversation Manager</h1>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '2rem', height: 'calc(100vh - 150px)' }}>
        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '1.5rem', overflowY: 'auto' }}>
          <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem' }}>Your Documents</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {files.length === 0 ? (
              <p style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>No documents uploaded yet</p>
            ) : (
              files.map(file => (
                <div
                  key={file.hash}
                  onClick={() => handleFileSelect(file)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '1rem',
                    background: selectedFile?.hash === file.hash ? '#3b82f6' : '#1e293b',
                    border: '1px solid #444',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ fontSize: '1.5rem' }}>
                    {file.filename.toLowerCase().endsWith('.pdf') ? '📄' : '📝'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem', wordBreak: 'break-word' }}>
                      {file.filename}
                    </div>
                    <div style={{ fontSize: '0.875rem', opacity: 0.7, fontFamily: 'monospace' }}>
                      {file.hash.substring(0, 8)}...
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div style={{ background: '#202123', border: '1px solid #444', borderRadius: '8px', padding: '1.5rem', overflowY: 'auto' }}>
          {!selectedFile ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af', fontSize: '1.1rem' }}>
              <p>Select a document to view its conversations</p>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #444' }}>
                <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Conversations for "{selectedFile.filename}"</h2>
              </div>

              <div>
                <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>All Conversations ({conversations.length})</h3>
                {conversations.length === 0 ? (
                  <p style={{ color: '#9ca3af', textAlign: 'center', padding: '2rem' }}>No conversations found for this document</p>
                ) : (
                  <div style={{ display: 'grid', gap: '1rem' }}>
                    {conversations.map((conv, index) => (
                      <div key={index} style={{ background: '#1e293b', border: '1px solid #444', borderRadius: '6px', padding: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                          <span style={{ background: '#3b82f6', color: 'white', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.875rem', fontWeight: '600' }}>
                            #{index + 1}
                          </span>
                          <button
                            onClick={() => handleDeleteConversation(conv.question)}
                            style={{
                              background: '#dc3545',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              padding: '0.25rem 0.5rem',
                              fontSize: '0.875rem'
                            }}
                            title="Delete this conversation"
                          >
                            ✕
                          </button>
                        </div>
                        <div style={{ marginBottom: '0.75rem', lineHeight: 1.5 }}>
                          <strong style={{ color: '#9ca3af', display: 'block', marginBottom: '0.25rem' }}>Question:</strong> 
                          {conv.question}
                        </div>
                        <div style={{ marginBottom: '0.75rem', lineHeight: 1.5 }}>
                          <strong style={{ color: '#9ca3af', display: 'block', marginBottom: '0.25rem' }}>Answer:</strong> 
                          {conv.answer}
                        </div>
                        {conv.confidence && (
                          <div style={{ marginBottom: '0.75rem', lineHeight: 1.5 }}>
                            <strong style={{ color: '#9ca3af', display: 'block', marginBottom: '0.25rem' }}>Confidence:</strong> 
                            {Math.round(conv.confidence * 100)}%
                          </div>
                        )}
                        {conv.created_at && (
                          <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                            <strong>Created:</strong> {new Date(conv.created_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}