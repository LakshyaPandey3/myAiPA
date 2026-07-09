// src/components/Navbar.jsx
// Navigation bar for myAiPA.
// Shows on all protected screens.
// Displays current user name and logout button.

import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const navLinks = [
    { path: '/dashboard', label: 'Home' },
    { path: '/tasks', label: 'Tasks' },
    { path: '/calendar', label: 'Calendar' },
    { path: '/eod', label: 'EOD Review' },
    { path: '/history', label: 'History' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <nav className="bg-white border-b border-gray-100 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">

        {/* Logo */}
        <Link to="/dashboard" className="text-xl font-bold text-indigo-600">
          myAiPA
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`text-sm font-medium transition-colors ${
                isActive(link.path)
                  ? 'text-indigo-600'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* User + logout */}
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            Hi, <span className="font-medium text-gray-800">{user?.username}</span>
          </span>
          <button
            onClick={logout}
            className="text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            Logout
          </button>
        </div>

      </div>
    </nav>
  )
}

export default Navbar