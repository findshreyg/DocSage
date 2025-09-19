import '../Styles/dashboard.css';
import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import DocumentViewer from '../components/DocumentViewer';

// PDF.js worker is now handled by the DocumentViewer component

export default function Dashboard() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [fileName, setFileName] = useState('');
  const [fileHash, setFileHash] = useState('');
  const [typingMessage, setTypingMessage] = useState(null);
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  const [isUploading, setIsUploading] = useState(false);
  // new state variables
  const [activeView, setActiveView] = useState('chat'); // 'chat' or 'key-value'
  const [adaptiveData, setAdaptiveData] = useState(null);
  const [isAdaptiveLoading, setIsAdaptiveLoading] = useState(false);

  // State for the PDF viewer and highlighting
  const [pdfUrl, setPdfUrl] = useState(null);
  const [, setPdfPageNumber] = useState(1);
  const [, setHighlightText] = useState(null);
  

  // Function to download file - let backend handle format conversion
  const downloadFile = async (conversation, token) => {
    console.log('Downloading file with file_hash:', conversation.fileHash);
    console.log('File name:', conversation.name);

    const response = await fetch('http://localhost:8002/file/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ file_hash: conversation.fileHash })
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('File download failed:', response.status, errorData);
      throw new Error(`Could not download file. Status: ${response.status}`);
    }

    const data = await response.json();
    console.log('File download successful:', data);
    return data.url;
  };

  useEffect(() => {
    const loadInitialFiles = async () => {
      const token = localStorage.getItem('docsage_token');
      if (!token) return navigate('/');

      try {
        const userRes = await fetch('http://localhost:8001/auth/get-user', { headers: { Authorization: `Bearer ${token}` } });
        if (!userRes.ok) throw new Error('Failed to fetch user');
        const userData = await userRes.json();
        setUser(userData);

        const listRes = await fetch('http://localhost:8002/file/list-uploads', { headers: { Authorization: `Bearer ${token}` } });
        if (!listRes.ok) throw new Error('Failed to fetch file list');
        const listData = await listRes.json();

        if (listData.files) {
          const formattedConversations = listData.files.map(file => ({
            id: file.hash,
            name: file.filename,
            fileHash: file.hash,
            messages: []
          }));
          setConversations(formattedConversations);
        }
      } catch (err) {
        console.error("Failed during initial data load:", err);
        localStorage.removeItem('docsage_token');
        navigate('/');
      }
    };
    loadInitialFiles();
  }, [navigate]);

  // const handleShowKeyValues = (conversation) => {
  //   // Switch the view immediately
  //   setActiveView('key-value');

  //   // If we already have the data, don't re-fetch
  //   if (adaptiveData && activeConversationId === conversation.id) {
  //       return;
  //   }

  //   setIsAdaptiveLoading(true);
  //   setAdaptiveData(null); // Clear old data

  //   const token = localStorage.getItem('docsage_token');
  //   let isCancelled = false;

  //   const fetchDetails = async () => {
  //       if (isCancelled) return;
  //       try {
  //           const res = await fetch(`http://localhost:8003/llm/get-extraction/${conversation.fileHash}`, {
  //               method: 'GET',
  //               headers: { 'Authorization': `Bearer ${token}` }
  //           });
  //           if (!res.ok) throw new Error('Failed to fetch details');

  //           const data = await res.json();
  //           if (data.status === 'processing') {
  //               setTimeout(fetchDetails, 5000);
  //           } else {
  //               setAdaptiveData(data);
  //               setIsAdaptiveLoading(false);
  //           }
  //       } catch (err) {
  //           if (!isCancelled) {
  //               console.error(err);
  //               setIsAdaptiveLoading(false);
  //           }
  //       }
  //   };

  //   fetchDetails();

  //   return () => { isCancelled = true; };
  //   };

  const handleShowKeyValues = async (conversation) => {
    // Set the active document and view immediately
    setActiveConversationId(conversation.id);
    setActiveView('key-value');
    setFileName(conversation.name);
    setFileHash(conversation.fileHash);

    // Clear previous data
    setPdfUrl(null);
    setAdaptiveData(null);
    setIsAdaptiveLoading(true);

    const token = localStorage.getItem('docsage_token');
    if (!token) return;

    try {
      // --- Logic from handleConversationClick to load the PDF ---
      // Download file and get URL
      const fileUrl = await downloadFile(conversation, token);
      setPdfUrl(fileUrl);
      // --- End of PDF loading logic ---

      // --- Existing logic to fetch adaptive data ---
      const fetchDetails = async () => {
        try {
          console.log('Fetching adaptive data for file_hash:', conversation.fileHash);
          const res = await fetch('http://localhost:8004/llm/extract-adaptive', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ file_hash: conversation.fileHash })
          });

          console.log('Adaptive data response status:', res.status);

          if (!res.ok) {
            const errorText = await res.text();
            console.error('Adaptive data fetch failed:', res.status, errorText);
            throw new Error('Failed to fetch details');
          }

          const data = await res.json();
          console.log('Adaptive data received:', data);

          if (data.status === 'processing') {
            console.log('Data still processing, retrying in 5 seconds...');
            setTimeout(fetchDetails, 5000);
          } else {
            console.log('Setting adaptive data:', data);
            setAdaptiveData(data);
            setIsAdaptiveLoading(false);
          }
        } catch (err) {
          console.error(err);
          setIsAdaptiveLoading(false);
        }
      };
      fetchDetails();
      // --- End of adaptive data logic ---

    } catch (err) {
      console.error("Failed to load key values view:", err);
      alert(`Could not load the document: ${err.message}`);
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem('docsage_token');
    try {
      await fetch('http://localhost:8001/auth/logout', {
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

  // const handleFileUpload = async (e) => {
  //   const file = e.target.files[0];
  //   if (!file) return;
  //   const token = localStorage.getItem('docsage_token');
  //   try {
  //     const formData = new FormData();
  //     formData.append('file', file);
  //     const uploadRes = await fetch('http://localhost:8002/file/upload', {
  //       method: 'POST',
  //       headers: { Authorization: `Bearer ${token}` },
  //       body: formData
  //     });
  //     if (!uploadRes.ok) throw new Error(`File upload failed with status ${uploadRes.status}`);
  //     const uploadData = await uploadRes.json();
  //     if (uploadData.message === 'File already uploaded.') {
  //       alert('This file has already been uploaded.');
  //       return;
  //     }
  //     const listRes = await fetch('http://localhost:8002/file/list-uploads', {
  //       headers: { Authorization: `Bearer ${token}` }
  //     });
  //     if (!listRes.ok) throw new Error(`Failed to fetch file list`);
  //     const listData = await listRes.json();
  //     const uploadedFileInfo = listData.files?.find(f => f.filename === file.name);
  //     if (!uploadedFileInfo || !uploadedFileInfo.hash) {
  //       throw new Error(`Could not find the hash for '${file.name}' in the list-uploads response.`);
  //     }
  //     const newFileHash = uploadedFileInfo.hash;
  //     setFileHash(newFileHash);
  //     const newConv = {
  //       id: newFileHash,
  //       name: file.name,
  //       messages: [],
  //       fileHash: newFileHash
  //     };
  //     setConversations(prev => [newConv, ...prev]);
  //     setActiveConversationId(newConv.id);
  //     setFileName(newConv.name);
  //   } catch (err) {
  //     console.error('An error occurred during the upload process:', err);
  //     alert('An error occurred during upload. Please check the console.');
  //   }
  // };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const token = localStorage.getItem('docsage_token');
    setIsUploading(true); // Show the loader

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Step 1: Upload the file and wait for the response
      const uploadRes = await fetch('http://localhost:8002/file/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (!uploadRes.ok) {
        // Handle cases where the upload itself fails
        const errData = await uploadRes.json();
        throw new Error(errData.detail || `File upload failed`);
      }

      const uploadData = await uploadRes.json();

      if (uploadData.message === 'File already uploaded.') {
        alert('This file has already been uploaded.');
        return; // Stop the process if it's a duplicate
      }

      // Step 2: Use the file_hash directly from the upload response
      const newFileHash = uploadData.file_hash;
      if (!newFileHash) {
        throw new Error("Server did not return a file_hash after upload.");
      }

      const newConv = {
        id: newFileHash,
        name: file.name,
        messages: [],
        fileHash: newFileHash
      };

      // Update the state with the new conversation
      setConversations(prev => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setFileName(newConv.name);
      setFileHash(newFileHash);

    } catch (err) {
      console.error('An error occurred during the upload process:', err);
      alert(`An error occurred during upload: ${err.message}`);
    } finally {
      setIsUploading(false); // Hide the loader
      // Reset the file input so you can upload the same file again if needed
      e.target.value = null;
    }
  };

  // const handleConversationClick = async (conversation) => {
  //   setActiveConversationId(conversation.id);
  //   setFileName(conversation.name);
  //   setFileHash(conversation.fileHash);
  //   setPdfUrl(null);
  //   setPdfPageNumber(1);
  //   setHighlightText(null);

  //   const token = localStorage.getItem('docsage_token');
  //   try {
  //     // Get the PDF URL
  //     const pdfUrlRes = await fetch('http://localhost:8002/file/download', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  //       body: JSON.stringify({ file_hash: conversation.fileHash })
  //     });
  //     if (!pdfUrlRes.ok) throw new Error('Could not get PDF download link.');
  //     const pdfData = await pdfUrlRes.json();
  //     setPdfUrl(pdfData.url);

  //     if (conversation.messages.length > 0) return;

  //     // CORRECTED: Fetch conversations using a query parameter
  //     const convRes = await fetch(`http://localhost:8001/conversation/get-file-conversations?file_hash=${conversation.fileHash}`, {
  //       method: 'GET',
  //       headers: { Authorization: `Bearer ${token}` }
  //     });
  //     if (!convRes.ok) throw new Error("Failed to fetch conversation history.");
  //     const data = await convRes.json();

  //     const fetchedMessages = [];
  //     if (data.conversations) {
  //       data.conversations.forEach(item => {
  //         fetchedMessages.push({ sender: 'user', text: item.question });
  //         fetchedMessages.push({ sender: 'ai', text: item.answer, source: item.source });
  //       });
  //     }
  //     setConversations(prevConvos => 
  //       prevConvos.map(c => 
  //         c.id === conversation.id ? { ...c, messages: fetchedMessages } : c
  //       )
  //     );
  //   } catch (err) {
  //     console.error("Failed to load conversation:", err);
  //     alert(`Could not load the document or its history: ${err.message}`);
  //   }
  // };

  const handleConversationClick = async (conversation) => {
    setActiveView('chat'); // Reset to chat view when a new document is clicked
    setAdaptiveData(null); // Clear old key-value data
    setActiveConversationId(conversation.id);
    setFileName(conversation.name);
    setFileHash(conversation.fileHash);
    setPdfUrl(null);
    setPdfPageNumber(1);
    setHighlightText(null);

    const token = localStorage.getItem('docsage_token');
    try {
      // Download file and get URL
      const fileUrl = await downloadFile(conversation, token);
      setPdfUrl(fileUrl);

      if (conversation.messages.length > 0) return;

      const convRes = await fetch(`http://localhost:8003/conversation/get-file-conversations?file_hash=${conversation.fileHash}`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!convRes.ok) throw new Error("Failed to fetch conversation history.");
      const data = await convRes.json();

      const fetchedMessages = [];
      if (data.conversations) {
        data.conversations.forEach(item => {
          let sourceData = null;
          // Robustly handle if source is a string or an object
          if (typeof item.source === 'string') {
            try { sourceData = JSON.parse(item.source); }
            catch (e) { console.error("Failed to parse source from history", e); }
          } else if (typeof item.source === 'object' && item.source !== null) {
            sourceData = item.source;
          }

          fetchedMessages.push({ sender: 'user', text: item.question });
          fetchedMessages.push({
            sender: 'ai',
            text: item.answer,
            source: sourceData,
            reasoning: item.reasoning,
            confidence: item.confidence
          });
        });
      }
      setConversations(prevConvos =>
        prevConvos.map(c =>
          c.id === conversation.id ? { ...c, messages: fetchedMessages } : c
        )
      );
    } catch (err) {
      console.error("Failed to load conversation:", err);
      alert(`Could not load the document or its history: ${err.message}`);
    }
  };

  // const handleSend = async (e) => {
  //   e.preventDefault();
  //   const input = e.target.elements.userInput.value;
  //   if (!input || !activeConversationId || !fileHash) return;

  //   const token = localStorage.getItem('docsage_token');
  //   const userMessage = { sender: 'user', text: input };

  //   setConversations(prev =>
  //     prev.map(conv =>
  //       conv.id === activeConversationId
  //         ? { ...conv, messages: [...conv.messages, userMessage] }
  //         : conv
  //     )
  //   );
  //   setTypingMessage('Thinking...');
  //   setHighlightText(null);

  //   try {
  //     const res = await fetch('http://localhost:8003/llm/ask', {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  //       body: JSON.stringify({ file_hash: fileHash, question: input })
  //     });

  //     if (!res.ok) throw new Error("LLM request failed");
  //     const data = await res.json();
  //     const aiMessage = { 
  //       sender: 'ai', 
  //       text: data.answer || 'No answer received.',
  //       source: data.source
  //     };

  //     setConversations(prev =>
  //       prev.map(conv =>
  //         conv.id === activeConversationId
  //           ? { ...conv, messages: [...conv.messages, aiMessage] }
  //           : conv
  //       )
  //     );
  //   } catch (err) {
  //     alert("Failed to get a response from the document.");
  //   } finally {
  //     setTypingMessage(null);
  //     e.target.reset();
  //   }
  // };


  const handleSend = async (e) => {
    e.preventDefault();
    const input = e.target.elements.userInput.value;
    if (!input || !activeConversationId || !fileHash) return;

    const token = localStorage.getItem('docsage_token');
    const userMessage = { sender: 'user', text: input };

    setConversations(prev =>
      prev.map(conv =>
        conv.id === activeConversationId
          ? { ...conv, messages: [...conv.messages, userMessage] }
          : conv
      )
    );
    setTypingMessage('Thinking...');
    setHighlightText(null);

    try {
      const res = await fetch('http://localhost:8004/llm/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ file_hash: fileHash, question: input })
      });

      if (!res.ok) throw new Error("LLM request failed");

      const data = await res.json();

      let sourceData = null;
      // Robustly handle if source is a string or an object
      if (typeof data.source === 'string') {
        try { sourceData = JSON.parse(data.source); }
        catch (e) { console.error("Failed to parse source from live response", e); }
      } else if (typeof data.source === 'object' && data.source !== null) {
        sourceData = data.source;
      }

      if (sourceData?.page_number && sourceData?.search_anchor) {
        setPdfPageNumber(sourceData.page_number);
        setHighlightText(sourceData.search_anchor);
      }

      const aiMessage = {
        sender: 'ai',
        text: data.answer || 'No answer received.',
        reasoning: data.reasoning,
        confidence: data.confidence,
        source: sourceData
      };

      setConversations(prev =>
        prev.map(conv =>
          conv.id === activeConversationId
            ? { ...conv, messages: [...conv.messages, aiMessage] }
            : conv
        )
      );
    } catch (err) {
      alert("Failed to get a response from the document.");
    } finally {
      setTypingMessage(null);
      e.target.reset();
    }
  };



  const handleNewChat = () => {
    setActiveConversationId(null);
    setFileName('');
    setFileHash('');
    setPdfUrl(null);
    setHighlightText(null);
  };

  const handleDelete = async (conversationId) => {
    const conversationToDelete = conversations.find(c => c.id === conversationId);
    if (!conversationToDelete) return;

    const confirmationText = 'confirm delete';
    const userInput = prompt(`To delete the document "${conversationToDelete.name}", please type the following exactly: ${confirmationText}`);

    // Immediately cancel if user hits escape or the prompt is empty
    if (!userInput) {
      return;
    }

    // Simple, reliable check
    if (userInput.toLowerCase() !== confirmationText) {
      alert("Deletion cancelled. The text did not match.");
      return;
    }

    // This part will now only run if the text matches
    try {
      const token = localStorage.getItem('docsage_token');
      const res = await fetch('http://localhost:8002/file/delete-file', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ file_hash: conversationToDelete.fileHash })
      });

      if (!res.ok) {
        throw new Error('Server failed to delete the file.');
      }

      const updatedConversations = conversations.filter(c => c.id !== conversationId);
      setConversations(updatedConversations);

      if (conversationId === activeConversationId) {
        handleNewChat();
      }

    } catch (err) {
      console.error("Delete failed:", err);
      alert("Could not delete the file. Please try again.");
    }
  };



  const activeConversation = conversations.find(c => c.id === activeConversationId);

  // Document viewer handles zoom functionality internally

  return (
    <div className="dashboard">
      <PanelGroup direction="horizontal">
        <Panel defaultSize={20} minSize={15}>
          <aside className="sidebar">
            <div className="sidebar-header">
              <h3>Documents</h3>
              <button className="new-chat-btn" onClick={handleNewChat}>+ New Chat</button>
            </div>
            <ul className="conversation-list">
              {conversations.map(conv => (
                // This is the ONLY <li> that should be inside your map function
                <li
                  key={conv.id}
                  className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
                >
                  <div className="conversation-name" onClick={() => handleConversationClick(conv)}>
                    <span className="file-icon">
                      {conv.name.toLowerCase().endsWith('.pdf') ? '📄' :
                        conv.name.toLowerCase().match(/\.(docx?|xlsx?|pptx?)$/i) ? '📝' : '📎'}
                    </span>
                    <span className="file-name">{conv.name}</span>
                  </div>

                  <div className="conversation-actions">
                    <button onClick={() => handleShowKeyValues(conv)} className="icon-btn" title="View Keypair Values">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="18" height="18">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
                      </svg>
                    </button>

                    <button className="icon-btn delete-btn" onClick={(e) => { e.stopPropagation(); handleDelete(conv.id); }} title="Delete Document">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="18" height="18">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </li>
                // <li
                //   key={conv.id}
                //   className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
                //   onClick={() => handleConversationClick(conv)}
                // >
                //   <div className="conversation-name">{conv.name}</div>
                //   <button className="delete-btn" onClick={(e) => { e.stopPropagation(); handleDelete(conv.id); }}>✕</button>
                // </li>


                //   <li
                //   key={conv.id}
                //   className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
                //   >
                //     <div className="conversation-main-action" onClick={() => handleConversationClick(conv)}>
                //         <div className="conversation-name">{conv.name}</div>
                //     </div>
                //     <div className="conversation-actions">
                //         {/* THIS IS THE NEW LINK */}
                //         <Link to={`/details/${conv.fileHash}`} className="details-link">Details</Link>
                //         <button className="delete-btn" onClick={(e) => { e.stopPropagation(); handleDelete(conv.id); }}>✕</button>
                //     </div>
                // </li>
              ))}
            </ul>
          </aside>
        </Panel>
        <PanelResizeHandle className="resize-handle" />
        <Panel>
          <main className="main-chat">
            <header className="chat-header">
              <div className="header-left">
                <nav className="main-nav">
                  <button onClick={() => navigate('/files')} className="nav-btn">
                    📁 File Manager
                  </button>
                  <button onClick={() => navigate('/conversations')} className="nav-btn">
                    💬 Conversations
                  </button>
                  <button onClick={() => navigate('/api-tester')} className="nav-btn">
                    🔧 API Tester
                  </button>
                  <button onClick={() => navigate('/help')} className="nav-btn">
                    ❓ Help
                  </button>
                </nav>
              </div>
              <div className="header-right">
                {user && (
                  <div className="user-dropdown">
                    <span onClick={() => setShowDropdown(!showDropdown)} style={{ cursor: 'pointer' }}>{user.name}</span>
                    {showDropdown && (
                      <div className="dropdown-menu">
                        <button onClick={() => navigate('/profile')}>Profile</button>
                        <button onClick={() => navigate('/settings')}>Settings</button>
                        <button onClick={handleLogout}>Logout</button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </header>

            {isUploading ? (
              <div className="loader-container">{/* Your loader JSX */}</div>
            ) : !activeConversationId ? (
              <div className="upload-box">
                <label htmlFor="fileUpload" className="upload-label">Upload a document</label>
                <input type="file" id="fileUpload" accept=".pdf,.docx,.png,.jpg" onChange={handleFileUpload} />
              </div>
            ) : (
              <PanelGroup direction="horizontal" className="chat-container">
                <Panel defaultSize={50} minSize={30} className="pdf-viewer-panel">
                  {pdfUrl ? (
                    <DocumentViewer
                      fileUrl={pdfUrl}
                      fileName={fileName}
                      onError={(error) => {
                        console.error('Document viewer error:', error);
                      }}
                    />
                  ) : (
                    <div className="loader-container">
                      <div className="loading-spinner">Loading document...</div>
                    </div>
                  )}
                </Panel>
                <PanelResizeHandle className="resize-handle" />
                <Panel defaultSize={50} minSize={30}>
                  <div className="right-panel">
                    {activeView === 'chat' ? (
                      // The Chat View
                      <div className="chat-panel">
                        <div className="messages">
                          {activeConversation?.messages.map((msg, idx) => (
                            <div key={idx} className={`message ${msg.sender}`}>
                              <div className="bubble">
                                <strong>{msg.sender === 'user' ? 'You' : 'DocSage'}:</strong> {msg.text}
                                {/* ... your source button and meta info JSX ... */}
                              </div>
                            </div>
                          ))}
                          {typingMessage && (<div className="message ai"><div className="bubble"><strong>DocSage:</strong> {typingMessage}</div></div>)}
                        </div>
                        <form onSubmit={handleSend} className="input-form">
                          <input type="text" name="userInput" placeholder="Ask something about the document..." />
                          <button type="submit">Send</button>
                        </form>
                      </div>
                    ) : (
                      // The Key-Value View
                      <div className="key-value-panel">
                        <h3>Extracted Key-Value Pairs</h3>
                        {isAdaptiveLoading ? (
                          <p>Loading extracted data...</p>
                        ) : adaptiveData && adaptiveData.adaptive_extraction ? (
                          <div className="adaptive-extraction-display">
                            {/* Classification Section */}
                            {adaptiveData.adaptive_extraction.classification && (
                              <div className="classification-section">
                                <h4>📋 Document Classification</h4>
                                <div className="classification-info">
                                  <div className="classification-item">
                                    <strong>Document Type:</strong> {adaptiveData.adaptive_extraction.classification.document_type}
                                  </div>
                                  <div className="classification-item">
                                    <strong>Description:</strong> {adaptiveData.adaptive_extraction.classification.description}
                                  </div>
                                  <div className="classification-item">
                                    <strong>Confidence:</strong> {Math.round(adaptiveData.adaptive_extraction.classification.confidence * 100)}%
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Field Values Section */}
                            {adaptiveData.adaptive_extraction.field_values && Object.keys(adaptiveData.adaptive_extraction.field_values).length > 0 && (
                              <div className="field-values-section">
                                <h4>🔍 Extracted Field Values</h4>
                                <div className="kv-grid">
                                  {Object.entries(adaptiveData.adaptive_extraction.field_values).map(([key, val]) => (
                                    <div className="kv-row" key={key}>
                                      <div className="kv-key">{key.replace(/_/g, ' ')}</div>
                                      <div className="kv-value">
                                        <div className="field-value">
                                          {typeof val.value === 'object' ? JSON.stringify(val.value, null, 2) : String(val.value ?? 'N/A')}
                                        </div>
                                        {val.confidence && (
                                          <div className="field-confidence">
                                            Confidence: {Math.round(val.confidence * 100)}%
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}


                          </div>
                        ) : (
                          <p>No adaptive extraction data available for this document.</p>
                        )}
                      </div>
                    )}
                  </div>
                </Panel>
              </PanelGroup>
            )}
          </main>
        </Panel>
      </PanelGroup>
    </div>
  );
}