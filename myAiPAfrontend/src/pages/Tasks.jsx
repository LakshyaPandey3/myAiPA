// src/pages/Tasks.jsx
// Full task management screen for myAiPA.
// Create, update status, and delete tasks.
// Color coded by priority — high=red, medium=yellow, low=green.

import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import api from '../api/axios'

function Tasks() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    priority: 'medium',
    due_date: '',
    description: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [formError, setFormError] = useState('')

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/tasks/')
      setTasks(response.data.data)
    } catch (err) {
      setError('Failed to load tasks.')
    } finally {
      setLoading(false)
    }
  }

  const handleFormChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setFormError('')
  }

  const handleCreateTask = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    setFormError('')

    try {
      const response = await api.post('/api/tasks/', formData)
      setTasks([response.data.data, ...tasks])
      setFormData({ title: '', priority: 'medium', due_date: '', description: '' })
      setShowForm(false)
    } catch (err) {
      const errors = err.response?.data?.errors
      if (errors) {
        const firstError = Object.values(errors)[0]
        setFormError(Array.isArray(firstError) ? firstError[0] : firstError)
      } else {
        setFormError('Failed to create task.')
      }
    } finally {
      setFormLoading(false)
    }
  }

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      const response = await api.patch(`/api/tasks/${taskId}/status/`, {
        status: newStatus,
      })
      setTasks(tasks.map(t =>
        t.id === taskId ? response.data.data : t
      ))
    } catch (err) {
      setError('Failed to update task status.')
    }
  }

  const handleDelete = async (taskId) => {
    try {
      await api.delete(`/api/tasks/${taskId}/`)
      setTasks(tasks.filter(t => t.id !== taskId))
    } catch (err) {
      setError('Failed to delete task.')
    }
  }

  const priorityColor = (priority) => {
    if (priority === 'high') return 'bg-red-100 text-red-700'
    if (priority === 'medium') return 'bg-yellow-100 text-yellow-700'
    return 'bg-green-100 text-green-700'
  }

  const priorityDot = (priority) => {
    if (priority === 'high') return 'bg-red-400'
    if (priority === 'medium') return 'bg-yellow-400'
    return 'bg-green-400'
  }

  const isOverdue = (task) => {
    if (!task.due_date || task.status === 'done') return false
    return task.due_date < new Date().toISOString().split('T')[0]
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-3xl mx-auto px-6 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
            <p className="text-gray-500 text-sm mt-1">
              {tasks.length} task{tasks.length !== 1 ? 's' : ''} total
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {showForm ? 'Cancel' : '+ Add Task'}
          </button>
        </div>

        {/* Add task form */}
        {showForm && (
          <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-6 shadow-sm">
            <h2 className="font-semibold text-gray-800 mb-4">New Task</h2>

            {formError && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateTask} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleFormChange}
                  placeholder="What do you need to do?"
                  required
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    name="priority"
                    value={formData.priority}
                    onChange={handleFormChange}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Due Date
                  </label>
                  <input
                    type="date"
                    name="due_date"
                    value={formData.due_date}
                    onChange={handleFormChange}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
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

              <button
                type="submit"
                disabled={formLoading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
              >
                {formLoading ? 'Creating...' : 'Create Task'}
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

        {/* Loading */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-400">Loading tasks...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No tasks yet.</p>
            <p className="text-gray-300 text-sm mt-1">
              Add your first task above.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => (
              <div
                key={task.id}
                className={`bg-white border rounded-2xl p-5 shadow-sm transition-opacity ${
                  task.status === 'done' ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-start gap-4">

                  {/* Priority dot */}
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 mt-1.5 ${priorityDot(task.priority)}`} />

                  {/* Task content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className={`font-medium text-gray-800 ${
                        task.status === 'done' ? 'line-through text-gray-400' : ''
                      }`}>
                        {task.title}
                      </p>

                      {/* Priority badge */}
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priorityColor(task.priority)}`}>
                        {task.priority}
                      </span>

                      {/* Overdue badge */}
                      {isOverdue(task) && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-100 text-red-600">
                          Overdue
                        </span>
                      )}
                    </div>

                    {task.description && (
                      <p className="text-sm text-gray-500 mt-1">
                        {task.description}
                      </p>
                    )}

                    {task.due_date && (
                      <p className="text-xs text-gray-400 mt-1">
                        Due: {new Date(task.due_date + 'T00:00:00').toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">

                    {/* Status selector */}
                    <select
                      value={task.status}
                      onChange={(e) => handleStatusChange(task.id, e.target.value)}
                      className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="done">Done</option>
                    </select>

                    {/* Delete button */}
                    <button
                      onClick={() => handleDelete(task.id)}
                      className="text-gray-300 hover:text-red-400 transition-colors text-lg leading-none"
                      title="Delete task"
                    >
                      ×
                    </button>

                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}

export default Tasks