// import '../styles/auth.css';
// import { useState } from 'react';
// import { useNavigate } from 'react-router-dom';

// export default function SignUp() {
//   const [email, setEmail] = useState('');
//   const [password, setPassword] = useState('');
//   const [name, setName] = useState('');
//   const [error, setError] = useState('');
//   const navigate = useNavigate();

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError('');
//     try {
//       const res = await fetch('http://localhost:8000/auth/signup', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ name, email, password })
//       });

//       if (!res.ok) {
//         const errData = await res.json();
//         throw new Error(errData.message || errData.detail || 'Signup failed');
//       }

//       navigate('/'); // Go to SignIn page after successful signup
//     } catch (err) {
//       setError(err.message);
//     }
//   };

//   return (
//     <div className="auth-container">
//       <h2>Sign Up</h2>
//       <form onSubmit={handleSubmit} className="auth-form">
//         <input
//           type="text"
//           placeholder="Full Name"
//           value={name}
//           onChange={e => setName(e.target.value)}
//           required
//         />
//         <input
//           type="email"
//           placeholder="Email"
//           value={email}
//           onChange={e => setEmail(e.target.value)}
//           required
//         />
//         <input
//           type="password"
//           placeholder="Password (min 8 chars, 1 number, 1 special char)"
//           value={password}
//           onChange={e => setPassword(e.target.value)}
//           required
//           pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$"
//           title="Password must be at least 8 characters long, include one number and one special character."
//         />
//         <button type="submit">Sign Up</button>
//       </form>
//       {error && <p className="error">{error}</p>}
//       <p>
//         Already have an account? <a href="/">Sign In</a>
//       </p>
//     </div>
//   );
// }

import '../Styles/auth.css';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function SignUp() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch('http://localhost:8001/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || errData.detail || 'Signup failed');
      }

      // NEW: Navigate to the OTP confirmation page with the user's email
      navigate('/confirm-signup', { state: { email: email } });
      
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Sign Up</h2>
        <input
          type="text"
          placeholder="Full Name"
          value={name}
          onChange={e => setName(e.target.value)}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password (min 8 chars, 1 number, 1 special char)"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          pattern="^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$"
          title="Password must be at least 8 characters long, include one number and one special character."
        />
        <button type="submit">Sign Up</button>
        {error && <p className="error">{error}</p>}
      </form>
      <p>
        Already have an account? <Link to="/">Sign In</Link>
      </p>
    </div>
  );
}