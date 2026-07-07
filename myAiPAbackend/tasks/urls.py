# tasks/urls.py
# This file defines all task management URL endpoints
# for myAiPA. Every URL here is prefixed with /api/tasks/
# because of how we include it in core/urls.py.

from django.urls import path
from .views import (
    TaskListCreateView,
    TaskDetailView,
    TodayTasksView,
    TaskStatusUpdateView,
)

urlpatterns = [
    # GET  /api/tasks/        → list all tasks
    # POST /api/tasks/        → create new task
    path('', TaskListCreateView.as_view(), name='task-list-create'),

    # GET today's and overdue tasks — must come BEFORE
    # {id} pattern otherwise 'today' gets matched as an id
    path('today/', TodayTasksView.as_view(), name='task-today'),

    # GET    /api/tasks/{id}/ → get single task
    # PATCH  /api/tasks/{id}/ → update task
    # DELETE /api/tasks/{id}/ → soft delete task
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),

    # PATCH /api/tasks/{id}/status/ → update status only
    path('<int:pk>/status/', TaskStatusUpdateView.as_view(), name='task-status'),
]