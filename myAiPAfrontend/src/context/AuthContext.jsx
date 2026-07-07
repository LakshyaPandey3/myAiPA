// src/context/AuthContext.jsx
// Global authentication state for myAiPA.
// Wraps the entire app so any component can access
// the current user and login/logout functions.
// Persists tokens in localStorage so user stays
// logged in after page refresh.

import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // On app load — check if tokens exist in localStorage.
  // If yes — fetch current user profile to restore session.
  // This keeps user logged in after page refresh.
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/api/auth/me/')
      setUser(response.data.data.user)
    } catch (error) {
      // Token invalid or expired — clear and logout
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = (userData, tokens) => {
    // Save tokens to localStorage for persistence
    localStorage.setItem('access_token', tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, fetchCurrentUser }}>
      {children}
    </AuthContext.Provider>
  )
}

// Custom hook — any component calls useAuth()
// to access user, login, logout, loading
export function useAuth() {
  return useContext(AuthContext)
}