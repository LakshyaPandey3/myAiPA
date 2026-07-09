import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'

function App() {
  const { user } = useAuth()

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={user ? <Navigate to="/dashboard" replace /> : <Login />}
        />
        <Route
          path="/register"
          element={user ? <Navigate to="/dashboard" replace /> : <Register />}
        />

        {/* Default redirect */}
        <Route
          path="/"
          element={<Navigate to={user ? '/dashboard' : '/login'} replace />}
        />

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* Coming soon placeholders */}
        <Route path="/tasks" element={<ProtectedRoute><div className="p-8">Tasks coming soon</div></ProtectedRoute>} />
        <Route path="/calendar" element={<ProtectedRoute><div className="p-8">Calendar coming soon</div></ProtectedRoute>} />
        <Route path="/eod" element={<ProtectedRoute><div className="p-8">EOD Review coming soon</div></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><div className="p-8">History coming soon</div></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App