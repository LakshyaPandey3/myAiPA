# briefing/urls.py
# This file defines all briefing URL endpoints
# for myAiPA. Every URL here is prefixed with
# /api/briefing/ from core/urls.py.

from django.urls import path
from .views import (
    MorningBriefingView,
    EODTasksView,
    EODSubmitView,
    NextDayPlanView,
    BriefingHistoryView,
)

urlpatterns = [
    # GET /api/briefing/morning/
    # Returns today's morning briefing — generates
    # if not yet done, returns cached if already done.
    path(
        'morning/',
        MorningBriefingView.as_view(),
        name='morning-briefing'
    ),

    # GET /api/briefing/eod/tasks/
    # Returns tasks for today's EOD review screen.
    path(
        'eod/tasks/',
        EODTasksView.as_view(),
        name='eod-tasks'
    ),

    # POST /api/briefing/eod/submit/
    # Submits today's EOD review with task completions.
    path(
        'eod/submit/',
        EODSubmitView.as_view(),
        name='eod-submit'
    ),

    # POST /api/briefing/nextday/
    # Saves tomorrow's goals and intention.
    path(
        'nextday/',
        NextDayPlanView.as_view(),
        name='next-day-plan'
    ),

    # GET /api/briefing/history/
    # Returns last 30 days of daily logs.
    path(
        'history/',
        BriefingHistoryView.as_view(),
        name='briefing-history'
    ),
]