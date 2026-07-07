# tasks/models.py
# This file defines the Task model for myAiPA.
# Tasks are the core of the daily productivity system.
# Every task belongs to a user and goes through
# a lifecycle from creation to completion.

from django.conf import settings
from django.db import models
from django.utils import timezone


"""
Custom manager for myAiPA Task model.
Automatically excludes soft deleted tasks from
all standard queries — Task.objects.all() will
never return deleted tasks unless explicitly requested.
This prevents deleted tasks from leaking to users
even if a view forgets to filter them out.
"""
class TaskManager(models.Manager):

    def get_queryset(self):
        """
        Override default queryset to exclude
        soft deleted tasks automatically.
        Every Task.objects query uses this by default.
        """
        return super().get_queryset().filter(
            is_deleted=False
        )

    def with_deleted(self):
        """
        Returns all tasks including deleted ones.
        Used by EOD review to account for tasks
        the user removed during the day.
        Zoya asks — why did you delete these tasks?
        """
        return super().get_queryset()

    def deleted_only(self):
        """
        Returns only deleted tasks.
        Used by EOD review to specifically surface
        tasks the user removed during the day.
        """
        return super().get_queryset().filter(
            is_deleted=True
        )


"""
Task model for myAiPA.
Represents a single task in a user's daily plan.
Used by the morning briefing, EOD review, and
next day planning features throughout myAiPA.
Every task belongs to exactly one user — users
can never see or modify each other's tasks.
completed_at is set automatically when status
changes to done — never set manually.
"""
class Task(models.Model):

    # Priority choices — controls task ordering
    # and how Zoya presents them in briefings.
    class Priority(models.TextChoices):
        HIGH   = 'high',   'High'
        MEDIUM = 'medium', 'Medium'
        LOW    = 'low',    'Low'

    # Status choices — tracks the task lifecycle
    # from creation through completion.
    class Status(models.TextChoices):
        TODO        = 'todo',        'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE        = 'done',        'Done'

    # The user this task belongs to.
    # CASCADE means if user is deleted — all their
    # tasks are deleted too. No orphaned data.
    # related_name='tasks' lets us do user.tasks.all()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
    )

    # What the task is. Required — every task
    # must have a title. Max 255 characters.
    title = models.CharField(max_length=255)

    # Optional extra context about the task.
    # User can leave this blank if title is enough.
    description = models.TextField(
        blank=True,
        default=''
    )

    # How important is this task.
    # Defaults to medium — most tasks are medium priority.
    # Zoya orders tasks by priority in morning briefing.
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    # When this task must be completed.
    # Optional — some tasks have no specific deadline.
    # null=True allows no date in database.
    # blank=True allows empty value in forms and API.
    due_date = models.DateField(
        null=True,
        blank=True,
    )

    # Current state of the task.
    # Starts as todo — moves to in_progress — then done.
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.TODO,
    )

    # Exact timestamp when task was marked done.
    # Set automatically in save() when status = done.
    # Reset to null if task is moved back from done.
    # Never set manually — always automatic.
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Soft delete flag — True means task is deleted.
    # We never hard delete tasks because EOD review
    # needs to account for tasks removed during the day.
    # Deleted tasks are hidden from user but kept in DB.
    is_deleted = models.BooleanField(default=False)

    # Automatically set when task is first created.
    # Never changes after that.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updated every time task is saved.
    # Used for incremental sync — "what changed recently?"
    updated_at = models.DateTimeField(auto_now=True)

    # Use our custom manager instead of default.
    # Task.objects.all() automatically excludes deleted.
    # Task.objects.with_deleted() includes deleted.
    # Task.objects.deleted_only() returns only deleted.
    objects = TaskManager()

    # Unfiltered manager — includes deleted tasks.
    # Used by admin panel and internal debugging only.
    # Never expose this to API endpoints.
    all_objects = models.Manager()

    class Meta:
        # Default ordering — most recently created first.
        ordering = ['-created_at']

        # Database indexes for frequently filtered fields.
        # Makes queries significantly faster at scale.
        indexes = [
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        """
        Override save to automatically manage completed_at.
        When status changes to done — set completed_at now.
        When status changes away from done — clear it.
        This ensures completed_at always reflects reality
        without any view or serializer needing to set it.
        """
        if self.status == self.Status.DONE:
            # Task just marked done — record exact time.
            # Only set if not already set — prevents
            # overwriting the original completion time
            # if task is saved again while still done.
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            # Task is not done — clear completion time.
            # Handles case where task moved back to todo.
            self.completed_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        # Display task in admin panel as
        # "username — task title"
        return f'{self.user.username} — {self.title}'