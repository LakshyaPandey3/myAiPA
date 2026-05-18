# tasks/admin.py
# Registers myAiPA's Task model with Django admin panel.
# Allows viewing and managing all tasks directly
# from the browser without touching the database.

from django.contrib import admin
from .models import Task


"""
Admin configuration for myAiPA's Task model.
Provides a clean interface for managing all tasks
across all users directly from the admin panel.
"""
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    # Columns shown in the task list view.
    list_display = (
        'title',
        'user',
        'priority',
        'status',
        'due_date',
        'is_deleted',
        'created_at',
    )

    # Filter buttons on the right side.
    list_filter = (
        'priority',
        'status',
        'is_deleted',
        'due_date',
    )

    # Search by title or username.
    search_fields = (
        'title',
        'user__username',
        'user__email',
    )

    # Default ordering — newest tasks first.
    ordering = ('-created_at',)

    # Read only fields — never manually changed.
    readonly_fields = (
        'created_at',
        'updated_at',
        'completed_at',
    )

    # Show 25 tasks per page.
    list_per_page = 25

    # Date navigation bar.
    date_hierarchy = 'created_at'