# scheduler/models.py
# This file defines the Event model for myAiPA.
# Events are scheduled blocks of time in a user's day.
# Unlike tasks which have due dates, events have
# specific start and end times that block the calendar.
# Zoya reads events alongside tasks to give intelligent
# daily briefings and suggest optimal work windows.

from django.conf import settings
from django.db import models


"""
Custom manager for myAiPA Event model.
Automatically excludes soft deleted events from
all standard queries — Event.objects.all() will
never return deleted events unless explicitly requested.
This prevents deleted events from leaking to users
even if a view forgets to filter them out.
"""
class EventManager(models.Manager):

    def get_queryset(self):
        """
        Override default queryset to exclude
        soft deleted events automatically.
        Every Event.objects query uses this by default.
        """
        return super().get_queryset().filter(
            is_deleted=False
        )

    def with_deleted(self):
        """
        Returns all events including deleted ones.
        Used by EOD review to account for events
        the user removed during the day.
        Zoya asks — why did you remove this event?
        """
        return super().get_queryset()

    def deleted_only(self):
        """
        Returns only deleted events.
        Used by EOD review to specifically surface
        events the user removed during the day.
        """
        return super().get_queryset().filter(
            is_deleted=True
        )


"""
Event model for myAiPA.
Represents a scheduled block of time in a user's day.
Used by morning briefing, conflict detection, EOD review
and next day planning throughout myAiPA.
Every event belongs to exactly one user — users
can never see or modify each other's events.
"""
class Event(models.Model):

    # The user this event belongs to.
    # CASCADE means if user is deleted — all their
    # events are deleted too. No orphaned data.
    # related_name='events' lets us do user.events.all()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events',
    )

    # What the event is. Required — every event
    # must have a title. Max 255 characters.
    title = models.CharField(max_length=255)

    # Optional extra details about the event.
    # User can leave this blank if title is enough.
    description = models.TextField(
        blank=True,
        default=''
    )

    # When the event starts — date and time combined.
    # Timezone aware — Django stores in UTC internally.
    # Displayed in user's local timezone by React.
    start_datetime = models.DateTimeField()

    # When the event ends — must be after start_datetime.
    # Validated in serializer to prevent end before start.
    end_datetime = models.DateTimeField()

    # Where the event takes place.
    # Optional — online meetings may have no location.
    location = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    # True if this event blocks the entire day.
    # Used for holidays, birthdays, all-day deadlines.
    # When True — Zoya knows the whole day is affected.
    is_all_day = models.BooleanField(default=False)

    # True if this event repeats on a schedule.
    # recurrence_rule stores how often it repeats.
    is_recurring = models.BooleanField(default=False)

    # How often this event recurs.
    # Examples: "every Monday", "daily", "every weekday"
    # Only meaningful when is_recurring=True.
    # Blank when is_recurring=False.
    recurrence_rule = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    # Soft delete flag — True means event is deleted.
    # We never hard delete events because EOD review
    # needs to account for events removed during the day.
    # Deleted events are hidden from user but kept in DB.
    is_deleted = models.BooleanField(default=False)

    # Automatically set when event is first created.
    # Never changes after that.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updated every time event is saved.
    # Used for incremental sync — "what changed recently?"
    updated_at = models.DateTimeField(auto_now=True)

    # Use custom manager — auto excludes deleted events.
    # Event.objects.all() never returns deleted events.
    # Event.objects.with_deleted() includes deleted.
    objects = EventManager()

    # Unfiltered manager for admin panel visibility.
    # Admin needs to see all events including deleted.
    all_objects = models.Manager()

    class Meta:
        # Default ordering — earliest events first.
        # Makes sense for calendar display — soonest
        # upcoming event should appear at the top.
        ordering = ['start_datetime']

        # Database indexes for frequently filtered fields.
        # Makes queries significantly faster at scale.
        indexes = [
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['user', 'start_datetime']),
            models.Index(fields=['user', 'end_datetime']),
            models.Index(fields=['user', 'start_datetime', 'end_datetime']),
        ]

    def __str__(self):
        # Display event in admin panel as
        # "username — event title"
        return f'{self.user.username} — {self.title}'