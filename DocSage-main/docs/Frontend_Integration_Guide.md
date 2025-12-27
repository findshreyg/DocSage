# 🎨 Frontend Integration Guide

This guide explains how the React frontend integrates with the DocSage backend services.

## 📋 Overview

The DocSage frontend is a modern React application built with Vite that provides a user-friendly interface for document processing and AI-powered Q&A. It communicates with the backend through a centralized API Gateway.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   API Gateway   │    │  Microservices  │
│  (Port 3000)    │◄──►│  (Port 8080)    │◄──►│  (Various Ports)│
│                 │    │                 │    │                 │
│ - User Interface│    │ - Request Proxy │    │ - Auth Service  │
│ - State Mgmt    │    │ - CORS Handling │    │ - File Service  │
│ - API Calls     │    │ - Load Balancing│    │ - LLM Service   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend services running (see Backend README)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 🔧 Configuration

### Environment Variables

The frontend uses these environment variables:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8080

# Application Name
VITE_APP_NAME=DocSage
```

### API Configuration

The API endpoints are centrally configured in `src/config/api.js`:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    // ... more endpoints
  },
  // ... other services
}
```

## 📱 Application Structure

### Pages

- **SignIn.jsx** - User authentication
- **SignUp.jsx** - User registration
- **Dashboard.jsx** - Main application interface
- **ConfirmSignUp.jsx** - Email verification
- **ForgotPassword.jsx** - Password reset request
- **ResetPassword.jsx** - Password reset form
- **AdaptiveDetailsPage.jsx** - Document details view

### Key Features

#### 1. Authentication Flow
```javascript
// Login example
const handleLogin = async (email, password) => {
  const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  localStorage.setItem('docsage_token', data.access_token);
};
```

#### 2. File Upload
```javascript
const handleFileUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(API_ENDPOINTS.FILE.UPLOAD, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
};
```

#### 3. Document Q&A
```javascript
const handleAskQuestion = async (fileHash, question) => {
  const response = await fetch(API_ENDPOINTS.LLM.ASK, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ file_hash: fileHash, question })
  });
};
```

## 🎨 UI Components

### Dashboard Layout

The main dashboard uses a resizable panel layout:

```jsx
<PanelGroup direction="horizontal">
  <Panel defaultSize={20} minSize={15}>
    {/* Sidebar with document list */}
  </Panel>
  <PanelResizeHandle />
  <Panel>
    <PanelGroup direction="horizontal">
      <Panel defaultSize={50}>
        {/* PDF Viewer */}
      </Panel>
      <PanelResizeHandle />
      <Panel defaultSize={50}>
        {/* Chat Interface */}
      </Panel>
    </PanelGroup>
  </Panel>
</PanelGroup>
```

### PDF Viewer Integration

Uses `@react-pdf-viewer/core` for PDF display:

```jsx
import { Viewer, Worker } from '@react-pdf-viewer/core';
import { zoomPlugin } from '@react-pdf-viewer/zoom';

const zoomPluginInstance = zoomPlugin();

<Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
  <Viewer 
    fileUrl={pdfUrl} 
    plugins={[zoomPluginInstance]}
  />
</Worker>
```

## 🔐 Authentication Integration

### Token Management

```javascript
// Store token after login
localStorage.setItem('docsage_token', accessToken);

// Include token in API requests
const token = localStorage.getItem('docsage_token');
headers: { 'Authorization': `Bearer ${token}` }

// Clear token on logout
localStorage.removeItem('docsage_token');
```

### Protected Routes

```jsx
// Check authentication status
useEffect(() => {
  const token = localStorage.getItem('docsage_token');
  if (!token) {
    navigate('/');
    return;
  }
  
  // Verify token with backend
  verifyToken(token);
}, []);
```

## 📡 API Integration

### Error Handling

```javascript
const apiCall = async (url, options) => {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, redirect to login
        localStorage.removeItem('docsage_token');
        navigate('/');
        return;
      }
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

### Loading States

```jsx
const [isLoading, setIsLoading] = useState(false);

const handleAction = async () => {
  setIsLoading(true);
  try {
    await apiCall();
  } finally {
    setIsLoading(false);
  }
};

return (
  <div>
    {isLoading ? <LoadingSpinner /> : <Content />}
  </div>
);
```

## 🎯 State Management

### Local State with Hooks

```jsx
// Document management
const [conversations, setConversations] = useState([]);
const [activeConversationId, setActiveConversationId] = useState(null);

// UI state
const [isUploading, setIsUploading] = useState(false);
const [showDropdown, setShowDropdown] = useState(false);

// PDF viewer state
const [pdfUrl, setPdfUrl] = useState(null);
const [pdfPageNumber, setPdfPageNumber] = useState(1);
```

### Data Flow

1. **Load Initial Data**: Fetch user info and document list on app start
2. **Document Selection**: Load PDF and conversation history
3. **Real-time Updates**: Update UI immediately, sync with backend
4. **Error Recovery**: Handle network errors gracefully

## 🔄 Development Workflow

### Hot Reload

Vite provides instant hot module replacement:

```bash
npm run dev
# Changes to React components update instantly
# API calls go to backend running on different port
```

### Build Process

```bash
# Development build
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## 🧪 Testing Integration

### Manual Testing

1. Start backend services
2. Start frontend: `npm run dev`
3. Test authentication flow
4. Upload a document
5. Ask questions about the document

### API Testing

Use the browser's Network tab to monitor API calls:

- Check request/response format
- Verify authentication headers
- Monitor error responses

## 🚀 Deployment

### Production Build

```bash
# Build for production
npm run build

# Serve static files
# The dist/ folder contains the built application
```

### Environment Configuration

For production deployment:

```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_APP_NAME=DocSage
```

## 🔧 Troubleshooting

### Common Issues

**CORS Errors**
- Ensure backend API Gateway has CORS configured
- Check that frontend URL is in allowed origins

**Authentication Issues**
- Verify token format and expiration
- Check that backend auth service is running

**File Upload Problems**
- Check file size limits
- Verify supported file types
- Monitor network requests for errors

**PDF Viewer Issues**
- Ensure PDF worker is loaded correctly
- Check browser console for PDF.js errors

### Debug Mode

Enable debug logging:

```javascript
// Add to your component
useEffect(() => {
  console.log('Current state:', { conversations, activeConversationId });
}, [conversations, activeConversationId]);
```

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [React PDF Viewer](https://react-pdf-viewer.dev/)
- [React Router](https://reactrouter.com/)

## 🤝 Contributing

When contributing to the frontend:

1. Follow React best practices
2. Use consistent naming conventions
3. Add proper error handling
4. Test with different document types
5. Ensure responsive design

## 📞 Support

For frontend-specific issues:

- Check browser console for errors
- Verify API endpoints are accessible
- Test with different browsers
- Check network connectivity

---

**Happy coding! 🚀**