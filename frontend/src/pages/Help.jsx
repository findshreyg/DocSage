import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../Styles/help.css';

export default function Help() {
    const [activeSection, setActiveSection] = useState('getting-started');
    const navigate = useNavigate();

    const sections = [
        { id: 'getting-started', title: 'Getting Started', icon: '🚀' },
        { id: 'uploading-files', title: 'Uploading Files', icon: '📁' },
        { id: 'asking-questions', title: 'Asking Questions', icon: '❓' },
        { id: 'managing-conversations', title: 'Managing Conversations', icon: '💬' },
        { id: 'key-value-extraction', title: 'Key-Value Extraction', icon: '🔍' },
        { id: 'file-management', title: 'File Management', icon: '📋' },
        { id: 'account-settings', title: 'Account Settings', icon: '⚙️' },
        { id: 'troubleshooting', title: 'Troubleshooting', icon: '🔧' },
        { id: 'api-reference', title: 'API Reference', icon: '📚' },
        { id: 'keyboard-shortcuts', title: 'Keyboard Shortcuts', icon: '⌨️' }
    ];

    const content = {
        'getting-started': {
            title: 'Getting Started with DocSage',
            content: (
                <div className="help-content">
                    <h3>Welcome to DocSage!</h3>
                    <p>DocSage is an intelligent document processing system that allows you to upload documents and ask questions about their content using AI.</p>

                    <h4>Quick Start Guide:</h4>
                    <ol>
                        <li><strong>Sign Up:</strong> Create your account using a valid email address</li>
                        <li><strong>Verify Email:</strong> Check your email for a verification code</li>
                        <li><strong>Upload Documents:</strong> Upload PDF, Word, Excel, or PowerPoint files</li>
                        <li><strong>Ask Questions:</strong> Start asking questions about your documents</li>
                        <li><strong>View Extractions:</strong> Use the key-value extraction feature for structured data</li>
                    </ol>

                    <h4>Supported File Types:</h4>
                    <ul>
                        <li>PDF (.pdf)</li>
                        <li>Microsoft Word (.doc, .docx)</li>
                        <li>Microsoft Excel (.xls, .xlsx)</li>
                        <li>Microsoft PowerPoint (.ppt, .pptx)</li>
                        <li>Images (.png, .jpg, .jpeg)</li>
                    </ul>

                    <div className="tip-box">
                        <strong>💡 Tip:</strong> For best results, ensure your documents have clear text and are not heavily image-based.
                    </div>
                </div>
            )
        },
        'uploading-files': {
            title: 'Uploading Files',
            content: (
                <div className="help-content">
                    <h3>How to Upload Files</h3>

                    <h4>From Dashboard:</h4>
                    <ol>
                        <li>Click the "Upload a document" area in the center of the dashboard</li>
                        <li>Select your file from the file browser</li>
                        <li>Wait for the upload to complete</li>
                        <li>Your file will appear in the sidebar</li>
                    </ol>

                    <h4>From File Manager:</h4>
                    <ol>
                        <li>Navigate to File Manager from the dashboard</li>
                        <li>Click "Upload Files" button</li>
                        <li>Select one or multiple files</li>
                        <li>Monitor upload progress</li>
                    </ol>

                    <h4>File Size Limits:</h4>
                    <ul>
                        <li>Maximum file size: 50MB per file</li>
                        <li>Multiple files can be uploaded simultaneously</li>
                        <li>Files are processed automatically after upload</li>
                    </ul>

                    <div className="warning-box">
                        <strong>⚠️ Note:</strong> Large files may take longer to process. Please be patient during the upload process.
                    </div>
                </div>
            )
        },
        'asking-questions': {
            title: 'Asking Questions',
            content: (
                <div className="help-content">
                    <h3>How to Ask Questions</h3>

                    <h4>Basic Question Asking:</h4>
                    <ol>
                        <li>Select a document from the sidebar</li>
                        <li>Type your question in the input field at the bottom</li>
                        <li>Press Enter or click "Send"</li>
                        <li>Wait for the AI to process and respond</li>
                    </ol>

                    <h4>Types of Questions You Can Ask:</h4>
                    <ul>
                        <li><strong>Factual:</strong> "What is the total amount mentioned in this invoice?"</li>
                        <li><strong>Summarization:</strong> "Can you summarize the main points of this document?"</li>
                        <li><strong>Analysis:</strong> "What are the key risks mentioned in this contract?"</li>
                        <li><strong>Comparison:</strong> "How does this year's performance compare to last year?"</li>
                        <li><strong>Extraction:</strong> "List all the dates mentioned in this document"</li>
                    </ul>

                    <h4>Best Practices:</h4>
                    <ul>
                        <li>Be specific in your questions</li>
                        <li>Ask one question at a time for better accuracy</li>
                        <li>Use clear, simple language</li>
                        <li>Reference specific sections if needed</li>
                    </ul>

                    <div className="tip-box">
                        <strong>💡 Tip:</strong> The AI provides confidence scores and reasoning for its answers. Check these for reliability.
                    </div>
                </div>
            )
        },
        'managing-conversations': {
            title: 'Managing Conversations',
            content: (
                <div className="help-content">
                    <h3>Conversation Management</h3>

                    <h4>Viewing Conversations:</h4>
                    <ul>
                        <li>All conversations are automatically saved</li>
                        <li>Click on a document to view its conversation history</li>
                        <li>Use the Conversation Manager for advanced management</li>
                    </ul>

                    <h4>Searching Conversations:</h4>
                    <ol>
                        <li>Go to Conversation Manager</li>
                        <li>Select a document</li>
                        <li>Use the search box to find specific questions</li>
                        <li>View matching conversations</li>
                    </ol>

                    <h4>Deleting Conversations:</h4>
                    <ul>
                        <li><strong>Single Conversation:</strong> Use the delete button next to specific conversations</li>
                        <li><strong>All Conversations:</strong> Use "Delete All Conversations" for a document</li>
                        <li><strong>Bulk Delete:</strong> Select multiple conversations in the manager</li>
                    </ul>

                    <div className="warning-box">
                        <strong>⚠️ Warning:</strong> Deleted conversations cannot be recovered. Use this feature carefully.
                    </div>
                </div>
            )
        },
        'key-value-extraction': {
            title: 'Key-Value Extraction',
            content: (
                <div className="help-content">
                    <h3>Automated Key-Value Extraction</h3>

                    <h4>What is Key-Value Extraction?</h4>
                    <p>This feature automatically identifies and extracts structured information from your documents, such as names, dates, amounts, and other key data points.</p>

                    <h4>How to Use:</h4>
                    <ol>
                        <li>Upload a document</li>
                        <li>Click the key icon (🔍) next to the document in the sidebar</li>
                        <li>Wait for the extraction process to complete</li>
                        <li>View the extracted data in a structured format</li>
                    </ol>

                    <h4>Types of Data Extracted:</h4>
                    <ul>
                        <li><strong>Document Classification:</strong> Type and category of document</li>
                        <li><strong>Key Fields:</strong> Important data points specific to document type</li>
                        <li><strong>Entities:</strong> Names, dates, locations, amounts</li>
                        <li><strong>Metadata:</strong> Document properties and characteristics</li>
                    </ul>

                    <h4>Best Document Types for Extraction:</h4>
                    <ul>
                        <li>Invoices and receipts</li>
                        <li>Contracts and agreements</li>
                        <li>Forms and applications</li>
                        <li>Reports and statements</li>
                    </ul>

                    <div className="tip-box">
                        <strong>💡 Tip:</strong> Extraction works best with well-formatted documents that have clear structure and labels.
                    </div>
                </div>
            )
        },
        'file-management': {
            title: 'File Management',
            content: (
                <div className="help-content">
                    <h3>Managing Your Files</h3>

                    <h4>File Manager Features:</h4>
                    <ul>
                        <li><strong>Upload Multiple Files:</strong> Select and upload several files at once</li>
                        <li><strong>Filter by Type:</strong> View files by category (PDF, Word, Excel, etc.)</li>
                        <li><strong>Sort Options:</strong> Sort by name, date, or size</li>
                        <li><strong>Bulk Operations:</strong> Select multiple files for batch operations</li>
                    </ul>

                    <h4>File Operations:</h4>
                    <ul>
                        <li><strong>Download:</strong> Get a secure download link for your files</li>
                        <li><strong>View Details:</strong> See file information and extracted data</li>
                        <li><strong>Delete:</strong> Remove files and all associated data</li>
                        <li><strong>Bulk Delete:</strong> Remove multiple files at once</li>
                    </ul>

                    <h4>File Information:</h4>
                    <p>For each file, you can view:</p>
                    <ul>
                        <li>File name and type</li>
                        <li>Upload date and time</li>
                        <li>File size</li>
                        <li>Unique file hash</li>
                        <li>Processing status</li>
                    </ul>

                    <div className="warning-box">
                        <strong>⚠️ Important:</strong> Deleting a file will also delete all associated conversations and extracted data.
                    </div>
                </div>
            )
        },
        'account-settings': {
            title: 'Account Settings',
            content: (
                <div className="help-content">
                    <h3>Managing Your Account</h3>

                    <h4>Profile Management:</h4>
                    <ul>
                        <li><strong>View Profile:</strong> See your account information</li>
                        <li><strong>Change Password:</strong> Update your login credentials</li>
                        <li><strong>Account Security:</strong> Manage security settings</li>
                    </ul>

                    <h4>Application Settings:</h4>
                    <ul>
                        <li><strong>Theme:</strong> Choose between dark, light, or auto themes</li>
                        <li><strong>Language:</strong> Select your preferred language</li>
                        <li><strong>Default View:</strong> Set chat or key-value as default</li>
                        <li><strong>File Limits:</strong> Configure maximum file sizes</li>
                    </ul>

                    <h4>Data Management:</h4>
                    <ul>
                        <li><strong>Export Settings:</strong> Download your configuration</li>
                        <li><strong>Import Settings:</strong> Restore from a backup</li>
                        <li><strong>Clear Cache:</strong> Remove stored data</li>
                    </ul>

                    <h4>Account Deletion:</h4>
                    <p>If you need to delete your account:</p>
                    <ol>
                        <li>Go to Profile settings</li>
                        <li>Scroll to the "Danger Zone"</li>
                        <li>Click "Delete Account"</li>
                        <li>Type the confirmation phrase exactly</li>
                        <li>Confirm deletion</li>
                    </ol>

                    <div className="warning-box">
                        <strong>⚠️ Warning:</strong> Account deletion is permanent and cannot be undone. All your data will be lost.
                    </div>
                </div>
            )
        },
        'troubleshooting': {
            title: 'Troubleshooting',
            content: (
        <div className="help-content">
          <h3>Common Issues and Solutions</h3>
          
          <h4>Upload Issues:</h4>
          <div className="troubleshoot-item"></div>      <strong>Problem:</strong> File won't upload
            <br />
            <strong>Solutions:</strong>
            <ul>
              <li>Check file size (must be under 50MB)</li>
              <li>Verify file type is supported</li>
              <li>Check your internet connection</li>
              <li>Try refreshing the page</li>
            </ul>
          </div>

          <h4>Login Issues:</h4>
          <div className="troubleshoot-item">
            <strong>Problem:</strong> Cannot log in
            <br />
            <strong>Solutions:</strong>
            <ul>
              <li>Verify email and password are correct</li>
              <li>Check if account is confirmed</li>
              <li>Use "Forgot Password" if needed</li>
              <li>Clear browser cache and cookies</li>
            </ul>
          </div>

          <h4>AI Response Issues:</h4>
          <div className="troubleshoot-item">
            <strong>Problem:</strong> AI not responding or giving poor answers
            <br />
            <strong>Solutions:</strong>
            <ul>
              <li>Make questions more specific</li>
              <li>Check document quality and text clarity</li>
              <li>Try rephrasing your question</li>
              <li>Ensure document is fully processed</li>
            </ul>
          </div>

          <h4>Performance Issues:</h4>
          <div className="troubleshoot-item">
            <strong>Problem:</strong> Slow loading or responses
            <br />
            <strong>Solutions:</strong>
            <ul>
              <li>Check your internet connection</li>
              <li>Close unnecessary browser tabs</li>
              <li>Clear browser cache</li>
              <li>Try using a different browser</li>
            </ul>
          </div>

          <div className="tip-box">
            <strong>💡 Still having issues?</strong> Check the service status in Settings or contact support.
          </div>
        </div >
      )
},
'api-reference': {
    title: 'API Reference',
        content: (
            <div className="help-content">
                <h3>API Endpoints Reference</h3>

                <h4>Authentication Endpoints:</h4>
                <div className="api-section">
                    <code>POST /auth/signup</code> - Create new account
                    <br />
                    <code>POST /auth/login</code> - User login
                    <br />
                    <code>POST /auth/logout</code> - User logout
                    <br />
                    <code>GET /auth/get-user</code> - Get user information
                    <br />
                    <code>POST /auth/change-password</code> - Change password
                    <br />
                    <code>DELETE /auth/delete-user</code> - Delete account
                </div>

                <h4>File Management Endpoints:</h4>
                <div className="api-section">
                    <code>POST /file/upload</code> - Upload file
                    <br />
                    <code>GET /file/list-uploads</code> - List user files
                    <br />
                    <code>POST /file/download</code> - Get download link
                    <br />
                    <code>DELETE /file/delete-file</code> - Delete file
                </div>

                <h4>Conversation Endpoints:</h4>
                <div className="api-section">
                    <code>GET /conversation/get-file-conversations</code> - Get conversations
                    <br />
                    <code>POST /conversation/find-conversation</code> - Search conversations
                    <br />
                    <code>DELETE /conversation/delete-conversation</code> - Delete conversation
                    <br />
                    <code>DELETE /conversation/delete-all-conversations</code> - Delete all
                </div>

                <h4>LLM Endpoints:</h4>
                <div className="api-section">
                    <code>POST /llm/ask</code> - Ask question about document
                    <br />
                    <code>POST /llm/extract-adaptive</code> - Extract key-value pairs
                </div>

                <div className="tip-box">
                    <strong>💡 Testing:</strong> Use the API Tester page to test these endpoints interactively.
                </div>
            </div>
        )
},
'keyboard-shortcuts': {
    title: 'Keyboard Shortcuts',
        content: (
            <div className="help-content">
                <h3>Keyboard Shortcuts</h3>

                <h4>General Navigation:</h4>
                <div className="shortcut-grid">
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>D</kbd>
                        <span>Go to Dashboard</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>U</kbd>
                        <span>Upload File</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>F</kbd>
                        <span>File Manager</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>M</kbd>
                        <span>Conversation Manager</span>
                    </div>
                </div>

                <h4>Chat Interface:</h4>
                <div className="shortcut-grid">
                    <div className="shortcut-item">
                        <kbd>Enter</kbd>
                        <span>Send Message</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Shift</kbd> + <kbd>Enter</kbd>
                        <span>New Line</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>K</kbd>
                        <span>Clear Chat</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>↑</kbd> / <kbd>↓</kbd>
                        <span>Navigate Messages</span>
                    </div>
                </div>

                <h4>Document Viewer:</h4>
                <div className="shortcut-grid">
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>+</kbd>
                        <span>Zoom In</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>-</kbd>
                        <span>Zoom Out</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Ctrl</kbd> + <kbd>0</kbd>
                        <span>Reset Zoom</span>
                    </div>
                    <div className="shortcut-item">
                        <kbd>Page Up</kbd> / <kbd>Page Down</kbd>
                        <span>Navigate Pages</span>
                    </div>
                </div>

                <div className="tip-box">
                    <strong>💡 Note:</strong> Some shortcuts may vary depending on your browser and operating system.
                </div>
            </div>
        )
}
  };

return (
    <div className="help-container">
        <div className="help-header">
            <button onClick={() => navigate('/dashboard')} className="back-btn">
                ← Back to Dashboard
            </button>
            <h1>Help & Documentation</h1>
        </div>

        <div className="help-content-wrapper">
            <div className="help-sidebar">
                <nav className="help-nav">
                    {sections.map(section => (
                        <button
                            key={section.id}
                            onClick={() => setActiveSection(section.id)}
                            className={`nav-item ${activeSection === section.id ? 'active' : ''}`}
                        >
                            <span className="nav-icon">{section.icon}</span>
                            <span className="nav-title">{section.title}</span>
                        </button>
                    ))}
                </nav>
            </div>

            <div className="help-main">
                <div className="help-section">
                    <h2>{content[activeSection].title}</h2>
                    {content[activeSection].content}
                </div>
            </div>
        </div>
    </div>
);
}