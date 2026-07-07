# scheduler/admin.py
# Registers myAiPA's Event model with Django admin panel.
# Allows viewing and managing all events directly
# from the browser without touching the database.

from django.contrib import admin
from .models import Event


"""
Admin configuration for myAiPA's Event model.
Provides a clean interface for managing all events
across all users directly from the admin panel.
"""
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        """
        Override admin queryset to show ALL events
        including soft deleted ones.
        Admin needs full visibility for debugging.
        """
        return Event.all_objects.all()

    # Columns shown in the event list view.
    list_display = (
        'title',
        'user',
        'start_datetime',
        'end_datetime',
        'is_all_day',
        'is_recurring',
        'is_deleted',
    )

    # Filter buttons on the right side.
    list_filter = (
        'is_all_day',
        'is_recurring',
        'is_deleted',
    )

    # Search by title, location or username.
    search_fields = (
        'title',
        'location',
        'user__username',
        'user__email',
    )

    # Default ordering — earliest events first.
    ordering = ('start_datetime',)

    # Read only fields — never manually changed.
    readonly_fields = (
        'created_at',
        'updated_at',
    )

    # Show 25 events per page.
    list_per_page = 25

    # Date navigation bar based on start time.
    date_hierarchy = 'start_datetime'