import { useState, useEffect } from 'react';
import { Viewer, Worker } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import { zoomPlugin } from '@react-pdf-viewer/zoom';
import '@react-pdf-viewer/zoom/lib/styles/index.css';

const DocumentViewer = ({ fileUrl, fileName, onError }) => {
  const [fileType, setFileType] = useState('unknown');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const zoomPluginInstance = zoomPlugin();
  const { ZoomIn, ZoomOut, Zoom } = zoomPluginInstance;

  // Determine file type from filename
  const getFileType = (filename) => {
    if (!filename) return 'unknown';
    const extension = filename.toLowerCase().split('.').pop();
    
    const fileTypes = {
      pdf: 'pdf',
      doc: 'document',
      docx: 'document',
      xls: 'spreadsheet',
      xlsx: 'spreadsheet',
      ppt: 'presentation',
      pptx: 'presentation',
      txt: 'text',
      jpg: 'image',
      jpeg: 'image',
      png: 'image',
      gif: 'image',
      bmp: 'image'
    };
    
    return fileTypes[extension] || 'unknown';
  };

  const getFileIcon = (filename) => {
    const type = getFileType(filename);
    const icons = {
      pdf: '📄',
      document: '📝',
      spreadsheet: '📊',
      presentation: '📋',
      text: '📄',
      image: '🖼️',
      unknown: '📎'
    };
    return icons[type] || icons.unknown;
  };

  const getFileTypeDescription = (filename) => {
    const type = getFileType(filename);
    const extension = filename.toLowerCase().split('.').pop().toUpperCase();
    
    const descriptions = {
      pdf: 'PDF Document',
      document: `${extension} Document`,
      spreadsheet: `${extension} Spreadsheet`,
      presentation: `${extension} Presentation`,
      text: 'Text File',
      image: `${extension} Image`,
      unknown: `${extension} File`
    };
    
    return descriptions[type] || descriptions.unknown;
  };

  useEffect(() => {
    if (fileName) {
      setFileType(getFileType(fileName));
      setIsLoading(false);
    }
  }, [fileName]);

  const handlePdfError = (error) => {
    console.error('PDF Viewer Error:', error);
    setError('This file cannot be displayed as a PDF. It may not be a PDF file or may be corrupted.');
    if (onError) onError(error);
  };

  const renderPdfViewer = () => (
    <div className="pdf-content-wrapper">
      <div className="pdf-toolbar">
        <h4>{fileName}</h4>
        <div className="zoom-controls">
          <ZoomOut>
            {(props) => <button onClick={props.onClick} title="Zoom Out">-</button>}
          </ZoomOut>
          <Zoom>
            {(props) => <span>{`${Math.round(props.scale * 100)}%`}</span>}
          </Zoom>
          <ZoomIn>
            {(props) => <button onClick={props.onClick} title="Zoom In">+</button>}
          </ZoomIn>
        </div>
      </div>
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
        <Viewer 
          fileUrl={fileUrl} 
          plugins={[zoomPluginInstance]}
          onDocumentLoadError={handlePdfError}
        />
      </Worker>
    </div>
  );

  const renderImageViewer = () => (
    <div className="image-viewer">
      <div className="pdf-toolbar">
        <h4>{fileName}</h4>
      </div>
      <div className="image-content">
        <img 
          src={fileUrl} 
          alt={fileName}
          style={{ maxWidth: '100%', height: 'auto' }}
          onError={() => setError('Unable to load image file.')}
        />
      </div>
    </div>
  );

  const renderUnsupportedFile = () => (
    <div className="unsupported-file-viewer">
      <div className="pdf-toolbar">
        <h4>{fileName}</h4>
      </div>
      <div className="unsupported-content">
        <div className="file-info">
          <div className="file-icon" style={{ fontSize: '4rem', marginBottom: '1rem' }}>
            {getFileIcon(fileName)}
          </div>
          <h3>{getFileTypeDescription(fileName)}</h3>
          <p>This file type cannot be previewed in the browser.</p>
          <div className="file-actions">
            <a 
              href={fileUrl} 
              download={fileName}
              className="download-btn"
              style={{
                display: 'inline-block',
                padding: '10px 20px',
                backgroundColor: '#007bff',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '5px',
                margin: '10px'
              }}
            >
              📥 Download File
            </a>
            <button 
              onClick={() => window.open(fileUrl, '_blank')}
              className="open-btn"
              style={{
                padding: '10px 20px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                margin: '10px',
                cursor: 'pointer'
              }}
            >
              🔗 Open in New Tab
            </button>
          </div>
          <div className="file-details">
            <p><strong>File Name:</strong> {fileName}</p>
            <p><strong>File Type:</strong> {getFileTypeDescription(fileName)}</p>
            <p><strong>Note:</strong> You can still ask questions about this document using the chat interface.</p>
          </div>
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="document-viewer-loading">
        <div className="loading-spinner">Loading document...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-viewer-error">
        <div className="pdf-toolbar">
          <h4>{fileName}</h4>
        </div>
        <div className="error-content">
          <div className="error-message">
            <h3>⚠️ Unable to Display File</h3>
            <p>{error}</p>
            <div className="error-actions">
              <a 
                href={fileUrl} 
                download={fileName}
                className="download-btn"
                style={{
                  display: 'inline-block',
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '5px',
                  margin: '10px'
                }}
              >
                📥 Download File Instead
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render appropriate viewer based on file type
  switch (fileType) {
    case 'pdf':
      return renderPdfViewer();
    case 'image':
      return renderImageViewer();
    default:
      return renderUnsupportedFile();
  }
};

export default DocumentViewer;