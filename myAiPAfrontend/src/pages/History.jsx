// src/pages/History.jsx
// Shows past daily logs for myAiPA.
// Each log shows the date, productivity score,
// morning briefing and EOD summary.

import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'

function History() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedLog, setExpandedLog] = useState(null)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/briefing/history/')
      setLogs(response.data.data)
    } catch (err) {
      setError('Failed to load history.')
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = (score) => {
    if (!score) return 'bg-gray-100 text-gray-500'
    if (score >= 8) return 'bg-green-100 text-green-700'
    if (score >= 5) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-600'
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-IN', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-3xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">History</h1>
          <p className="text-gray-500 text-sm mt-1">
            Your past daily logs and reflections
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-400">Loading history...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No history yet.</p>
            <p className="text-gray-300 text-sm mt-1">
              Complete your first EOD review to see it here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {logs.map((log, index) => (
              <div
                key={index}
                className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden"
              >
                {/* Log header */}
                <div
                  className="flex items-center justify-between p-5 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => setExpandedLog(
                    expandedLog === index ? null : index
                  )}
                >
                  <div className="flex items-center gap-4">
                    {/* Score badge */}
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0 ${scoreColor(log.productivity_score)}`}>
                      {log.productivity_score || '—'}
                    </div>

                    <div>
                      <p className="font-medium text-gray-800">
                        {formatDate(log.date)}
                      </p>
                      <div className="flex items-center gap-3 mt-0.5">
                        {log.morning_briefing_generated && (
                          <span className="text-xs text-indigo-500">
                            ✓ Briefing
                          </span>
                        )}
                        {log.eod_submitted && (
                          <span className="text-xs text-green-500">
                            ✓ EOD Done
                          </span>
                        )}
                        {log.next_day_goals?.length > 0 && (
                          <span className="text-xs text-purple-500">
                            ✓ Plan Set
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <span className="text-gray-300 text-lg">
                    {expandedLog === index ? '↑' : '↓'}
                  </span>
                </div>

                {/* Expanded details */}
                {expandedLog === index && (
                  <div className="border-t border-gray-100 p-5 space-y-4">

                    {/* Morning briefing */}
                    {log.morning_briefing && (
                      <div>
                        <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wide mb-2">
                          Morning Briefing
                        </p>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          {log.morning_briefing}
                        </p>
                      </div>
                    )}

                    {/* EOD summary */}
                    {log.eod_summary && (
                      <div>
                        <p className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-2">
                          EOD Summary
                        </p>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          {log.eod_summary}
                        </p>
                      </div>
                    )}

                    {/* Next day goals */}
                    {log.next_day_goals?.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-2">
                          Goals Set for Next Day
                        </p>
                        <div className="space-y-1">
                          {log.next_day_goals.map((goal, i) => (
                            <div key={i} className="flex items-center gap-2">
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                goal.priority === 'high'
                                  ? 'bg-red-100 text-red-600'
                                  : goal.priority === 'medium'
                                  ? 'bg-yellow-100 text-yellow-600'
                                  : 'bg-green-100 text-green-600'
                              }`}>
                                {goal.priority}
                              </span>
                              <p className="text-sm text-gray-700">{goal.goal}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Intention */}
                    {log.next_day_intention && (
                      <div>
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
                          Intention
                        </p>
                        <p className="text-sm text-gray-500 italic">
                          "{log.next_day_intention}"
                        </p>
                      </div>
                    )}

                  </div>
                )}
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}

export default History