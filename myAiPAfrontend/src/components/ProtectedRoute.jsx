// src/components/ProtectedRoute.jsx
// Blocks unauthenticated access to protected screens.
// If user is not logged in — redirects to login page.
// Shows loading spinner while checking auth status.

import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  // Still checking if user is logged in — show nothing
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500 text-lg">Loading myAiPA...</p>
      </div>
    )
  }

  // Not logged in — redirect to login
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Logged in — show the protected screen
  return children
}

export default ProtectedRoute