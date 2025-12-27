import '../Styles/auth.css';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function ResetPassword() {
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email;

const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError("Email not found. Please start the password reset process again.");
      return;
    }

    try {
      // Create the data object that will be sent
      const requestBody = {
        email: email,
        code: code,
        new_password: newPassword
      };

      // This line will print the exact data to your browser's console
      console.log("Sending to server:", requestBody);

      const res = await fetch('http://localhost:8001/auth/confirm-forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!res.ok) {
        const errData = await res.json();
        let errorMessage = 'Password reset failed';
        if (errData.detail && Array.isArray(errData.detail)) {
            errorMessage = errData.detail[0].msg;
        } else if (errData.detail) {
            errorMessage = errData.detail;
        }
        throw new Error(errorMessage);
      }
      
      alert('Password has been reset successfully. Please sign in with your new password.');
      navigate('/');

    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Reset Your Password</h2>
        <p>A reset code was sent to {email || 'your email'}.</p>
        <input
          type="text"
          placeholder="Reset Code"
          value={code}
          onChange={e => setCode(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="New Password"
          value={newPassword}
          // This line is now corrected
          onChange={e => setNewPassword(e.target.value)}
          required
        />
        <button type="submit">Reset Password</button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  );
}