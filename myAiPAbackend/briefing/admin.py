# briefing/admin.py
# Registers myAiPA's DailyLog and TaskCompletion
# models with Django admin panel.
# Allows viewing and managing all briefing data
# directly from the browser without touching the
# database — essential for debugging during development.

from django.contrib import admin

from .models import DailyLog, TaskCompletion


"""
Admin configuration for myAiPA's DailyLog model.
Shows one complete day's data per user — morning
briefing, EOD summary, next day planning, score.
"""
@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):

    # Columns shown in the daily log list view.
    list_display = (
        'user',
        'date',
        'morning_briefing_generated',
        'eod_submitted',
        'productivity_score',
        'created_at',
    )

    # Filter buttons on the right side.
    list_filter = (
        'morning_briefing_generated',
        'eod_submitted',
        'date',
    )

    # Search by username or email.
    search_fields = (
        'user__username',
        'user__email',
    )

    # Most recent logs first.
    ordering = ('-date',)

    # Read only fields — never manually changed.
    readonly_fields = (
        'created_at',
        'updated_at',
    )

    # Show 25 logs per page.
    list_per_page = 25

    # Date navigation by log date.
    date_hierarchy = 'date'


"""
Admin configuration for myAiPA's TaskCompletion model.
Shows what happened to each task during EOD review —
whether it was done, and the reason if not.
"""
@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):

    # Columns shown in the task completion list view.
    list_display = (
        'task',
        'daily_log',
        'completed',
        'recorded_at',
    )

    # Filter by completion status.
    list_filter = (
        'completed',
    )

    # Search by task title or username.
    search_fields = (
        'task__title',
        'daily_log__user__username',
    )

    # Most recent first.
    ordering = ('-recorded_at',)

    # Read only fields.
    readonly_fields = ('recorded_at',)

    # Show 25 per page.
    list_per_page = 25
