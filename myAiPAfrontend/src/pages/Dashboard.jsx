// src/pages/Dashboard.jsx
// Main dashboard for myAiPA.
// Shows Zoya's morning briefing, today's tasks
// and today's events. The first thing the user
// sees every morning.

import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'

function Dashboard() {
  const { user } = useAuth()

  const [briefing, setBriefing] = useState(null)
  const [todayTasks, setTodayTasks] = useState([])
  const [todayEvents, setTodayEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // Fetch all three in parallel for speed
      const [briefingRes, tasksRes, eventsRes] = await Promise.all([
        api.get('/api/briefing/morning/'),
        api.get('/api/tasks/today/'),
        api.get('/api/events/today/'),
      ])

      setBriefing(briefingRes.data.data)
      setTodayTasks([
        ...tasksRes.data.data.today,
        ...tasksRes.data.data.overdue,
      ])
      setTodayEvents(eventsRes.data.data)
    } catch (err) {
      setError('Failed to load dashboard. Please refresh.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex items-center justify-center h-96">
          <p className="text-gray-400 text-lg">
            Zoya is preparing your briefing...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-4xl mx-auto px-6 py-8">

        {/* Morning greeting */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Good morning, {user?.username} 👋
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-6 text-sm">
            {error}
          </div>
        )}

        {/* Zoya's briefing card */}
        {briefing && (
          <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">Z</span>
              </div>
              <span className="text-sm font-medium text-indigo-700">
                {user?.myAiPA_name || 'Zoya'} — Morning Briefing
              </span>
            </div>
            <p className="text-gray-700 leading-relaxed text-sm">
              {briefing.briefing}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Today's tasks */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">Today's Tasks</h2>
              <a href="/tasks" className="text-xs text-indigo-600 hover:underline">
                View all
              </a>
            </div>

            {todayTasks.length === 0 ? (
              <p className="text-gray-400 text-sm">
                No tasks for today. Enjoy your day!
              </p>
            ) : (
              <div className="space-y-3">
                {todayTasks.slice(0, 5).map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3"
                  >
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      task.priority === 'high'
                        ? 'bg-red-400'
                        : task.priority === 'medium'
                        ? 'bg-yellow-400'
                        : 'bg-green-400'
                    }`} />
                    <span className={`text-sm ${
                      task.status === 'done'
                        ? 'line-through text-gray-400'
                        : 'text-gray-700'
                    }`}>
                      {task.title}
                    </span>
                    {task.due_date < new Date().toISOString().split('T')[0] && task.status !== 'done' && (
                      <span className="text-xs text-red-500 ml-auto">
                        Overdue
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Today's events */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-800">Today's Events</h2>
              <a href="/calendar" className="text-xs text-indigo-600 hover:underline">
                View all
              </a>
            </div>

            {todayEvents.length === 0 ? (
              <p className="text-gray-400 text-sm">
                No events scheduled today.
              </p>
            ) : (
              <div className="space-y-3">
                {todayEvents.map((event) => (
                  <div key={event.id} className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-indigo-400 flex-shrink-0 mt-1.5" />
                    <div>
                      <p className="text-sm text-gray-700 font-medium">
                        {event.title}
                      </p>
                      <p className="text-xs text-gray-400">
                        {new Date(event.start_datetime).toLocaleTimeString(
                          'en-IN',
                          { hour: '2-digit', minute: '2-digit' }
                        )}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* EOD Review button */}
        <div className="mt-6 text-center">

           <a href="/eod"
            className="inline-block bg-gray-900 hover:bg-gray-800 text-white font-medium px-6 py-3 rounded-xl text-sm transition-colors"
          >
            Start EOD Review →
           </a>

        </div>

      </div>
    </div>
  )
}

export default Dashboard