import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../Styles/ProfilePage.css';

export default function ProfilePage() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState({ type: '', text: '' });
  const [activeView, setActiveView] = useState('menu'); // 'menu', 'changePassword', 'deleteAccount'
  const navigate = useNavigate();

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    if (newPassword !== confirmPassword) {
      setMessage({ type: 'error', text: 'New passwords do not match.' });
      return;
    }

    const token = localStorage.getItem('docsage_token');
    if (!token) {
      navigate('/');
      return;
    }

    try {
      const response = await fetch('http://localhost:8001/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to change password.');
      }

      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setActiveView('menu'); // Go back to menu on success
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    }
  };

const handleDeleteAccount = async () => {
  const confirmation = window.confirm(
    'Are you absolutely sure you want to delete your account? This action is irreversible and will delete all your documents and conversations permanently.'
  );

  if (!confirmation) {
    return;
  }

  const token = localStorage.getItem('docsage_token');
  if (!token) {
    navigate('/');
    return;
  }

  try {
      const response = await fetch('http://127.0.0.1:8001/auth/delete-user', {
      method: 'DELETE', 
      headers: { 'Authorization': `Bearer ${token}` } 
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.message || 'Failed to delete account.');
    }

    // On successful deletion, log the user out and redirect to home
    localStorage.removeItem('docsage_token');
    alert('Your account has been successfully deleted.');
    navigate('/');
  } catch (err) {
    setMessage({ type: 'error', text: err.message });
  }
};
  
  // Renders the main menu
  const renderMenu = () => (
    <div className="profile-menu">
      <button onClick={() => { setMessage({ type: '', text: '' }); setActiveView('changePassword'); }} className="btn btn-secondary">
        Change Password
      </button>
      <button onClick={() => { setMessage({ type: '', text: '' }); setActiveView('deleteAccount'); }} className="btn btn-danger">
        Delete Account
      </button>
    </div>
  );

  // Renders the change password form
  const renderChangePassword = () => (
    <div className="profile-section">
      <h3 style={{ textAlign: 'center' }}>Change your Password</h3>
      <form onSubmit={handleChangePassword}>
        <div className="form-group">
          <label htmlFor="oldPassword" style={{ color: '#e6ece8ff' }}>Current Password</label>
          <input type="password" id="oldPassword" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="newPassword">New Password</label>
          <input type="password" id="newPassword" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm New Password</label>
          <input type="password" id="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
        </div>
      <div className="form-actions">
        <button type="submit" className="btn btn-primary">Update Password</button>
        <button type="button" onClick={() => setActiveView('menu')} className="btn btn-secondary">Back</button>
      </div>
      </form>
    </div>
  );

  // Renders the delete account section
  const renderDeleteAccount = () => (
    <div className="profile-section danger-zone">
      <h3>Delete Account</h3>
      <p>This will permanently delete your account and all associated data, including your documents and conversations. This action cannot be undone.</p>
      <button onClick={handleDeleteAccount} className="btn btn-danger">Delete My Account</button>
      <button onClick={() => setActiveView('menu')} className="btn btn-secondary">Back</button>
    </div>
  );

  return (
    <>
      <div className="profile-page-container">
        <div className="profile-card">
          <h2>Account Settings</h2>

          {/* Conditionally render the view based on state */}
          {activeView === 'menu' && renderMenu()}
          {activeView === 'changePassword' && renderChangePassword()}
          {activeView === 'deleteAccount' && renderDeleteAccount()}
          
          {message.text && (
            <div className={`message-display ${message.type}`}>
              {message.text}
            </div>
          )}
        </div>
      </div>
      <button onClick={() => navigate('/dashboard')} className="back-to-dashboard">
        Back to Dashboard
      </button>
    </>
  );
}
