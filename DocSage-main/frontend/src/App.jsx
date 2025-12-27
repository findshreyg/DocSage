import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Dashboard from './pages/Dashboard'
import ConfirmSignUp from './pages/ConfirmSignUp'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import AdaptiveDetailsPage from './pages/AdaptiveDetailsPage'
import ProfilePage from './pages/ProfilePage'
import FilesPage from './pages/FilesPage'
import ConversationsPage from './pages/ConversationsPage'
import APITestPage from './pages/APITestPage'
import SettingsPage from './pages/SettingsPage'
import Help from './pages/Help'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/confirm-signup" element={<ConfirmSignUp />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/details/:fileHash" element={<AdaptiveDetailsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/conversations" element={<ConversationsPage />} />
          <Route path="/files" element={<FilesPage />} />
          <Route path="/api-tester" element={<APITestPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/help" element={<Help />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
