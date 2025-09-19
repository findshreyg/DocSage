import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import Dashboard from './pages/Dashboard.jsx';
import ConfirmSignUp from './pages/ConfirmSignUp.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import ResetPassword from './pages/ResetPassword.jsx';
import AdaptiveDetailsPage from './pages/AdaptiveDetailsPage';

ReactDOM.createRoot(document.getElementById('root')).render(
  // <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/confirm-signup" element={<ConfirmSignUp />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/details/:fileHash" element={<AdaptiveDetailsPage />} />
      </Routes>
    </Router>
  // </React.StrictMode>
);