// import '../styles/auth.css';
// import { useState } from 'react';
// import { useNavigate } from 'react-router-dom';

// export default function SignIn() {
//   const [email, setEmail] = useState('');
//   const [password, setPassword] = useState('');
//   const [error, setError] = useState('');
//   const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError('');
//     try {
//       const res = await fetch('http://localhost:8000/auth/login', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ email, password })
//       });

//       if (!res.ok) {
//         const errData = await res.json();
//         throw new Error(errData.message || errData.detail || 'Login failed');
//       }

//       const data = await res.json();
//       localStorage.setItem('docsage_token', data.access_token);
//       localStorage.setItem('email', email);
//       navigate('/dashboard');
//     } catch (err) {
//       setError(err.message);
//     }
//   };

//   return (
//     <div className="auth-container">
//       <h2>Sign In</h2>
//       <form onSubmit={handleSubmit} className="auth-form">
//         <input
//           type="email"
//           placeholder="Email"
//           value={email}
//           onChange={e => setEmail(e.target.value)}
//           required
//         />
//         <input
//           type="password"
//           placeholder="Password"
//           value={password}
//           onChange={e => setPassword(e.target.value)}
//           required
//         />
//         <button type="submit">Sign In</button>
//       </form>
//       {error && <p className="error">{error}</p>}
//       <p>
//         Don't have an account? <a href="/signup">Sign Up</a>
//       </p>
//     </div>
//   );
// }


import '../Styles/auth.css';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function SignIn() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch('http://localhost:8001/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || errData.detail || 'Login failed');
      }

      const data = await res.json();
      localStorage.setItem('docsage_token', data.access_token);
      localStorage.setItem('email', email);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Sign In</h2>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
        />
        <button type="submit">Sign In</button>
        {error && <p className="error">{error}</p>}
        {/* NEW: Forgot Password Link */}
        <div className="auth-links">
            <Link to="/forgot-password">Forgot Password?</Link>
        </div>
      </form>
      <p>
        Don't have an account? <Link to="/signup">Sign Up</Link>
      </p>
    </div>
  );
}