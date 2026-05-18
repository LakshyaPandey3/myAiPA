# tasks/models.py
# This file defines the Task model for myAiPA.
# Tasks are the core of the daily productivity system.
# Every task belongs to a user and goes through
# a lifecycle from creation to completion.

from django.conf import settings
from django.db import models


"""
Task model for myAiPA.
Represents a single task in a user's daily plan.
Used by the morning briefing, EOD review, and
next day planning features throughout myAiPA.
Every task belongs to exactly one user — users
can never see or modify each other's tasks.
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
    # Null until the task is completed.
    # Used by EOD review to analyse completion patterns —
    # "you complete most tasks before noon."
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

    class Meta:
        # Default ordering — most recently created first.
        # Can be overridden in views when needed.
        ordering = ['-created_at']

        # Database index on user + is_deleted combination.
        # Most queries filter by both — index makes them fast.
        indexes = [
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        # Display task in admin panel as
        # "username — task title"
        return f'{self.user.username} — {self.title}'