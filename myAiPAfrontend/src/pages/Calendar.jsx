// src/pages/Calendar.jsx
// Events and calendar management screen for myAiPA.
// Create, view and delete scheduled events.
// Shows conflict warnings when events overlap.

import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'

function Calendar() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')
  const [conflicts, setConflicts] = useState([])
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    start_datetime: '',
    end_datetime: '',
    location: '',
    is_all_day: false,
    is_recurring: false,
    recurrence_rule: '',
  })

  useEffect(() => {
    fetchEvents()
  }, [])

  const fetchEvents = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/events/')
      setEvents(response.data.data)
    } catch (err) {
      setError('Failed to load events.')
    } finally {
      setLoading(false)
    }
  }

  const handleFormChange = (e) => {
    const value = e.target.type === 'checkbox'
      ? e.target.checked
      : e.target.value
    setFormData({ ...formData, [e.target.name]: value })
    setFormError('')
    setConflicts([])
  }

  const handleCreateEvent = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    setFormError('')
    setConflicts([])

    try {
      const response = await api.post('/api/events/', formData)
      setEvents([response.data.data, ...events])

      // Show conflict warning if any
      if (response.data.conflicts) {
        setConflicts(response.data.conflicts)
      }

      setFormData({
        title: '',
        description: '',
        start_datetime: '',
        end_datetime: '',
        location: '',
        is_all_day: false,
        is_recurring: false,
        recurrence_rule: '',
      })
      setShowForm(false)
    } catch (err) {
      const errors = err.response?.data?.errors
      if (errors) {
        const firstError = Object.values(errors)[0]
        setFormError(Array.isArray(firstError) ? firstError[0] : firstError)
      } else {
        setFormError('Failed to create event.')
      }
    } finally {
      setFormLoading(false)
    }
  }

  const handleDelete = async (eventId) => {
    try {
      await api.delete(`/api/events/${eventId}/`)
      setEvents(events.filter(e => e.id !== eventId))
    } catch (err) {
      setError('Failed to delete event.')
    }
  }

  const formatDateTime = (datetime) => {
    return new Date(datetime).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-3xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>
            <p className="text-gray-500 text-sm mt-1">
              {events.length} event{events.length !== 1 ? 's' : ''} scheduled
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {showForm ? 'Cancel' : '+ Add Event'}
          </button>
        </div>

        {/* Conflict warning */}
        {conflicts.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 mb-6">
            <p className="text-yellow-800 text-sm font-medium mb-1">
              ⚠️ Event created but overlaps with:
            </p>
            {conflicts.map((c) => (
              <p key={c.id} className="text-yellow-700 text-sm">
                — {c.title}
              </p>
            ))}
          </div>
        )}

        {/* Add event form */}
        {showForm && (
          <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-6 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-4">New Event</h2>

            {formError && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateEvent} className="space-y-4">

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleFormChange}
                  placeholder="Meeting with team"
                  required
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start *
                  </label>
                  <input
                    type="datetime-local"
                    name="start_datetime"
                    value={formData.start_datetime}
                    onChange={handleFormChange}
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End *
                  </label>
                  <input
                    type="datetime-local"
                    name="end_datetime"
                    value={formData.end_datetime}
                    onChange={handleFormChange}
                    required
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location (optional)
                </label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleFormChange}
                  placeholder="Office / Zoom / etc."
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleFormChange}
                  placeholder="Any extra details..."
                  rows={2}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                />
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    name="is_all_day"
                    checked={formData.is_all_day}
                    onChange={handleFormChange}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">All day</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    name="is_recurring"
                    checked={formData.is_recurring}
                    onChange={handleFormChange}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Recurring</span>
                </label>
              </div>

              {formData.is_recurring && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recurrence Rule *
                  </label>
                  <input
                    type="text"
                    name="recurrence_rule"
                    value={formData.recurrence_rule}
                    onChange={handleFormChange}
                    placeholder="e.g. every Monday, daily, every weekday"
                    required={formData.is_recurring}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={formLoading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
              >
                {formLoading ? 'Creating...' : 'Create Event'}
              </button>

            </form>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
            {error}
          </div>
        )}

        {/* Events list */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-400">Loading events...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No events scheduled.</p>
            <p className="text-gray-300 text-sm mt-1">
              Add your first event above.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div
                key={event.id}
                className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-indigo-400 flex-shrink-0 mt-1.5" />
                    <div>
                      <p className="font-medium text-gray-800">{event.title}</p>

                      <p className="text-xs text-gray-400 mt-1">
                        {event.is_all_day
                          ? 'All day'
                          : `${formatDateTime(event.start_datetime)} → ${formatDateTime(event.end_datetime)}`
                        }
                      </p>

                      {event.location && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          📍 {event.location}
                        </p>
                      )}

                      {event.is_recurring && (
                        <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                          Recurring: {event.recurrence_rule}
                        </span>
                      )}

                      {event.description && (
                        <p className="text-sm text-gray-500 mt-1">
                          {event.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(event.id)}
                    className="text-gray-300 hover:text-red-400 transition-colors text-lg leading-none flex-shrink-0"
                    title="Delete event"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}

export default Calendar