// src/pages/EODReview.jsx
// End of Day Review screen for myAiPA.
// Multi-step flow: accountability check → Zoya's summary
// → next day planning → Zoya's closing message.

import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'

function EODReview() {
  const { user } = useAuth()

  // Steps: 'loading' | 'already_submitted' | 'review' | 'summary' | 'nextday' | 'done'
  const [step, setStep] = useState('loading')
  const [tasks, setTasks] = useState([])
  const [overdueTasks, setOverdueTasks] = useState([])
  const [completions, setCompletions] = useState({})
  const [reasons, setReasons] = useState({})
  const [eodSummary, setEodSummary] = useState('')
  const [productivityScore, setProductivityScore] = useState(null)
  const [submitLoading, setSubmitLoading] = useState(false)
  const [error, setError] = useState('')

  // Next day plan state
  const [goals, setGoals] = useState([
    { goal: '', priority: 'high' },
    { goal: '', priority: 'medium' },
    { goal: '', priority: 'low' },
  ])
  const [intention, setIntention] = useState('')
  const [planLoading, setPlanLoading] = useState(false)
  const [closingMessage, setClosingMessage] = useState('')

  useEffect(() => {
    fetchEODTasks()
  }, [])

  const fetchEODTasks = async () => {
    try {
      const response = await api.get('/api/briefing/eod/tasks/')
      const data = response.data.data

      if (data.already_submitted) {
        setStep('already_submitted')
        return
      }

      const allTasks = data.today || []
      const overdueList = data.overdue || []

      setTasks(allTasks)
      setOverdueTasks(overdueList)

      // Initialize completions — default all to false
      const initCompletions = {}
      const initReasons = {}
      ;[...allTasks, ...overdueList].forEach(task => {
        initCompletions[task.id] = task.status === 'done'
        initReasons[task.id] = ''
      })
      setCompletions(initCompletions)
      setReasons(initReasons)

      if (allTasks.length === 0 && overdueList.length === 0) {
        setStep('review')
      } else {
        setStep('review')
      }
    } catch (err) {
      setError('Failed to load today\'s tasks.')
      setStep('review')
    }
  }

  const handleCompletionChange = (taskId, completed) => {
    setCompletions({ ...completions, [taskId]: completed })
    if (completed) {
      setReasons({ ...reasons, [taskId]: '' })
    }
  }

  const handleReasonChange = (taskId, reason) => {
    setReasons({ ...reasons, [taskId]: reason })
  }

  const handleSubmitEOD = async () => {
    setSubmitLoading(true)
    setError('')

    const allTasks = [...tasks, ...overdueTasks]
    const completionsData = allTasks.map(task => ({
      task_id: task.id,
      completed: completions[task.id] || false,
      reason_if_not: completions[task.id] ? '' : (reasons[task.id] || ''),
    }))

    try {
      const response = await api.post('/api/briefing/eod/submit/', {
        completions: completionsData,
      })

      setEodSummary(response.data.data.summary)
      setProductivityScore(response.data.data.productivity_score)
      setStep('summary')
    } catch (err) {
      setError('Failed to submit EOD review. Please try again.')
    } finally {
      setSubmitLoading(false)
    }
  }

  const handleGoalChange = (index, field, value) => {
    const updated = [...goals]
    updated[index][field] = value
    setGoals(updated)
  }

  const handleSubmitNextDay = async () => {
    const validGoals = goals.filter(g => g.goal.trim().length > 0)

    if (validGoals.length === 0) {
      setError('Please add at least one goal for tomorrow.')
      return
    }

    if (!intention.trim()) {
      setError('Please write your intention for tomorrow.')
      return
    }

    setPlanLoading(true)
    setError('')

    try {
      const response = await api.post('/api/briefing/nextday/', {
        goals: validGoals,
        intention: intention.trim(),
      })

      setClosingMessage(response.data.data.closing_message)
      setStep('done')
    } catch (err) {
      setError('Failed to save next day plan. Please try again.')
    } finally {
      setPlanLoading(false)
    }
  }

  const scoreColor = (score) => {
    if (!score) return 'text-gray-500'
    if (score >= 8) return 'text-green-600'
    if (score >= 5) return 'text-yellow-600'
    return 'text-red-500'
  }

  const allTasksList = [...tasks, ...overdueTasks]

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-2xl mx-auto px-6 py-8">

        {/* Already submitted */}
        {step === 'already_submitted' && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">✅</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              EOD Review Done
            </h1>
            <p className="text-gray-500">
              You've already submitted your review for today.
              See you tomorrow!
            </p>
          </div>
        )}

        {/* Loading */}
        {step === 'loading' && (
          <div className="text-center py-16">
            <p className="text-gray-400">Loading today's tasks...</p>
          </div>
        )}

        {/* Step 1 — Review tasks */}
        {step === 'review' && (
          <div>
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-gray-900">
                End of Day Review
              </h1>
              <p className="text-gray-500 mt-1 text-sm">
                Let's reflect on your day. How did it go?
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
                {error}
              </div>
            )}

            {allTasksList.length === 0 ? (
              <div className="bg-white border border-gray-100 rounded-2xl p-8 text-center mb-6">
                <p className="text-gray-400">
                  No tasks were planned for today.
                </p>
              </div>
            ) : (
              <div className="space-y-4 mb-6">
                {allTasksList.map((task) => (
                  <div
                    key={task.id}
                    className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-gray-800">
                            {task.title}
                          </p>
                          {task.due_date < new Date().toISOString().split('T')[0] && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-600">
                              Overdue
                            </span>
                          )}
                        </div>

                        {/* Done / Not done buttons */}
                        <div className="flex gap-3 mt-3">
                          <button
                            onClick={() => handleCompletionChange(task.id, true)}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                              completions[task.id]
                                ? 'bg-green-500 text-white'
                                : 'bg-gray-100 text-gray-600 hover:bg-green-50'
                            }`}
                          >
                            ✓ Done
                          </button>
                          <button
                            onClick={() => handleCompletionChange(task.id, false)}
                            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                              !completions[task.id]
                                ? 'bg-red-100 text-red-600'
                                : 'bg-gray-100 text-gray-600 hover:bg-red-50'
                            }`}
                          >
                            ✗ Not done
                          </button>
                        </div>

                        {/* Reason if not done */}
                        {!completions[task.id] && (
                          <div className="mt-3">
                            <input
                              type="text"
                              value={reasons[task.id] || ''}
                              onChange={(e) => handleReasonChange(task.id, e.target.value)}
                              placeholder="What happened? (optional)"
                              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={handleSubmitEOD}
              disabled={submitLoading}
              className="w-full bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 text-white font-medium py-3 rounded-xl text-sm transition-colors"
            >
              {submitLoading
                ? 'Zoya is reflecting on your day...'
                : 'Submit Review →'
              }
            </button>
          </div>
        )}

        {/* Step 2 — EOD Summary */}
        {step === 'summary' && (
          <div>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                Zoya's Reflection
              </h1>
            </div>

            {/* Score */}
            {productivityScore && (
              <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-4 text-center">
                <p className="text-sm text-gray-500 mb-1">
                  Today's productivity score
                </p>
                <p className={`text-5xl font-bold ${scoreColor(productivityScore)}`}>
                  {productivityScore}
                  <span className="text-2xl text-gray-300">/10</span>
                </p>
              </div>
            )}

            {/* Zoya's summary */}
            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">Z</span>
                </div>
                <span className="text-sm font-medium text-indigo-700">
                  {user?.myAiPA_name || 'Zoya'}
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed text-sm">
                {eodSummary}
              </p>
            </div>

            <button
              onClick={() => setStep('nextday')}
              className="w-full bg-gray-900 hover:bg-gray-800 text-white font-medium py-3 rounded-xl text-sm transition-colors"
            >
              Plan Tomorrow →
            </button>
          </div>
        )}

        {/* Step 3 — Next day planning */}
        {step === 'nextday' && (
          <div>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                Plan Tomorrow
              </h1>
              <p className="text-gray-500 mt-1 text-sm">
                Set your top goals and intention for tomorrow.
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 mb-4 text-sm">
                {error}
              </div>
            )}

            {/* Goals */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-4 shadow-sm">
              <h2 className="font-semibold text-gray-800 mb-4">
                Top 3 Goals for Tomorrow
              </h2>

              <div className="space-y-3">
                {goals.map((goal, index) => (
                  <div key={index} className="flex gap-3">
                    <input
                      type="text"
                      value={goal.goal}
                      onChange={(e) => handleGoalChange(index, 'goal', e.target.value)}
                      placeholder={`Goal ${index + 1}${index === 0 ? ' (most important)' : ''}`}
                      className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <select
                      value={goal.priority}
                      onChange={(e) => handleGoalChange(index, 'priority', e.target.value)}
                      className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Intention */}
            <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-6 shadow-sm">
              <h2 className="font-semibold text-gray-800 mb-2">
                One Intention
              </h2>
              <p className="text-gray-400 text-xs mb-3">
                How do you want to feel at the end of tomorrow?
              </p>
              <textarea
                value={intention}
                onChange={(e) => setIntention(e.target.value)}
                placeholder="I want to feel accomplished and focused..."
                rows={3}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
            </div>

            <button
              onClick={handleSubmitNextDay}
              disabled={planLoading}
              className="w-full bg-gray-900 hover:bg-gray-800 disabled:bg-gray-300 text-white font-medium py-3 rounded-xl text-sm transition-colors"
            >
              {planLoading
                ? 'Zoya is writing your closing message...'
                : 'Save Plan →'
              }
            </button>
          </div>
        )}

        {/* Step 4 — Done */}
        {step === 'done' && (
          <div>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">
                Goodnight 🌙
              </h1>
            </div>

            {/* Zoya's closing message */}
            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">Z</span>
                </div>
                <span className="text-sm font-medium text-indigo-700">
                  {user?.myAiPA_name || 'Zoya'}
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed text-sm">
                {closingMessage}
              </p>
            </div>

            <div className="text-center">

               <a href="/dashboard"
                className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-6 py-3 rounded-xl text-sm transition-colors"
              >
                Back to Dashboard
              </a>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

export default EODReview