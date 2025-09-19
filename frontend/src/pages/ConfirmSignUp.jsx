import '../Styles/auth.css';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function ConfirmSignUp() {
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  
  const location = useLocation();
  const email = location.state?.email;

  // Handles the final OTP confirmation
  const handleConfirm = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!email) {
      setError("Email not found. Please sign up again.");
      return;
    }
    
    try {
      const res = await fetch('http://localhost:8001/auth/confirm-signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, code: otp })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || errData.detail || 'Confirmation failed');
      }
      
      // On success, redirect to the login page
      alert('Account confirmed successfully! Please sign in.');
      navigate('/');

    } catch (err) {
      setError(err.message);
    }
  };
  
  // Handles the request to resend an OTP
  const handleResend = async () => {
    setError('');
    setMessage('');
    if (!email) {
      setError("Email not found. Please sign up again.");
      return;
    }

    try {
      const res = await fetch('http://localhost:8001/auth/resend-confirmation-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email })
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || errData.detail || 'Could not resend code');
      }

      setMessage("A new confirmation code has been sent to your email.");

    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleConfirm} className="auth-form">
        <h2>Confirm Your Account</h2>
        <p>An OTP has been sent to {email || 'your email'}.</p>
        <input
          type="text"
          placeholder="Confirmation Code"
          value={otp}
          onChange={e => setOtp(e.target.value)}
          required
        />
        <button type="submit">Confirm Account</button>
        {error && <p className="error">{error}</p>}
        {message && <p>{message}</p>}
      </form>
      <p>
        Didn't receive a code? <button type="button" onClick={handleResend} className="link-button">Resend</button>
      </p>
    </div>
  );
}