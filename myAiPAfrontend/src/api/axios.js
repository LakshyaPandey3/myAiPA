// src/api/axios.js
// Base Axios configuration for myAiPA.
// Every API call in the app uses this instance —
// never import axios directly anywhere else.
// JWT token is automatically attached to every request.
// 401 responses automatically redirect to login.

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// REQUEST INTERCEPTOR
// Runs before every request is sent.
// Reads the access token from localStorage and
// attaches it to the Authorization header automatically.
// The user never has to manually attach tokens.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// RESPONSE INTERCEPTOR
// Runs after every response comes back.
// If Django returns 401 (token expired or invalid) —
// clear tokens and redirect to login automatically.
// User never sees a cryptic error — they just get
// sent back to the login screen cleanly.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api