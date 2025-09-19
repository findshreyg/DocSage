import '../Styles/auth.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
      // Make the actual API call to the backend
      const res = await fetch('http://localhost:8001/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || errData.detail || 'Failed to send reset code');
      }

      // On success, notify the user and navigate to the next step
      setMessage('A reset code has been sent to your email.');
      
      // Navigate to the reset password page after a short delay
      setTimeout(() => {
        navigate('/reset-password', { state: { email: email } });
      }, 2000);

    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Forgot Password</h2>
        <p>Enter your email to receive a password reset code.</p>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <button type="submit">Send Reset Code</button>
        {error && <p className="error">{error}</p>}
        {message && <p>{message}</p>}
      </form>
    </div>
  );
}