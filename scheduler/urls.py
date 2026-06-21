# scheduler/urls.py
# This file defines all event management URL endpoints
# for myAiPA. Every URL here is prefixed with /api/events/
# because of how we include it in core/urls.py.

from django.urls import path
from .views import (
    EventListCreateView,
    EventDetailView,
    TodayEventsView,
)

urlpatterns = [
    # GET  /api/events/        → list all events
    # POST /api/events/        → create new event
    path('', EventListCreateView.as_view(), name='event-list-create'),

    # GET today's events — must come BEFORE {id} pattern
    # otherwise 'today' gets matched as an id
    path('today/', TodayEventsView.as_view(), name='event-today'),

    # GET    /api/events/{id}/ → get single event
    # PATCH  /api/events/{id}/ → update event
    # DELETE /api/events/{id}/ → soft delete event
    path('<int:pk>/', EventDetailView.as_view(), name='event-detail'),
]