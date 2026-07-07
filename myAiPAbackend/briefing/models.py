# briefing/models.py
# This file defines the DailyLog and TaskCompletion
# models for myAiPA's briefing system.
# DailyLog stores one complete day's data per user —
# morning briefing, EOD summary, next day planning.
# TaskCompletion records what happened to each task
# during the EOD accountability review.
#
# next_day_goals stores a structured JSON list where
# each goal has both text and priority — this lets
# Zoya distinguish what matters most in the next
# morning's briefing rather than treating all goals
# equally. Format:
# [
#   {"goal": "finish Django project", "priority": "high"},
#   {"goal": "call dentist", "priority": "medium"},
#   {"goal": "gym", "priority": "low"}
# ]
# Validated and enforced in the briefing serializer.

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from tasks.models import Task


"""
Stores one complete day's briefing data per user.
One record is created per user per day — never more.
Morning briefing is generated once and reused if the
user opens the app multiple times in the same morning.
EOD summary and next day plan are added later in the day.
next_day_goals stores structured goals with priorities
so Zoya can distinguish importance in the next briefing.
"""
class DailyLog(models.Model):

    # The user this daily log belongs to.
    # CASCADE — if user deleted, their logs deleted too.
    # related_name allows user.daily_logs.all()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_logs',
    )

    # The date this log represents.
    # One log per user per day — enforced by
    # unique_together in Meta below at database level.
    date = models.DateField()

    # The morning briefing Zoya generated for this day.
    # Blank until generated — generated once and reused
    # on all subsequent requests for the same day.
    morning_briefing = models.TextField(
        blank=True,
        default=''
    )

    # Whether the morning briefing has been generated.
    # True = already generated, return cached version.
    # False = not yet generated, generate and save now.
    # Prevents calling Groq API multiple times per day
    # for the same user — one generation per day only.
    morning_briefing_generated = models.BooleanField(
        default=False
    )

    # The EOD summary Zoya generated after the user
    # submitted their accountability review.
    # Blank until EOD review is submitted.
    eod_summary = models.TextField(
        blank=True,
        default=''
    )

    # Whether the EOD review has been submitted today.
    # Prevents the user from submitting EOD review
    # multiple times for the same day — once submitted,
    # the day is locked for accountability integrity.
    eod_submitted = models.BooleanField(default=False)

    # Tomorrow's top goals stored as a structured
    # JSON list. Each item has "goal" (text) and
    # "priority" (high/medium/low) so Zoya can
    # distinguish importance in the next morning's
    # briefing. Validated in the briefing serializer.
    # Example:
    # [
    #   {"goal": "finish project", "priority": "high"},
    #   {"goal": "call dentist", "priority": "medium"},
    #   {"goal": "gym", "priority": "low"}
    # ]
    # default=list means starts as empty list [].
    next_day_goals = models.JSONField(
        default=list,
        blank=True,
    )

    # One sentence describing how the user wants to
    # feel at the end of tomorrow. Surfaced by Zoya
    # in the next morning's briefing — closes the
    # daily loop and makes the PA feel personal.
    # Example: "I want to feel like I made real
    # progress on the project."
    next_day_intention = models.TextField(
        blank=True,
        default=''
    )

    # AI-generated productivity score for the day.
    # Set by Zoya during EOD review.
    # Enforced as 1 to 10 at database level via
    # validators — no invalid scores can ever be
    # stored regardless of how they arrive.
    # Null until EOD review is submitted.
    productivity_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ]
    )

    # When this log was first created.
    created_at = models.DateTimeField(auto_now_add=True)

    # When this log was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One log per user per day — enforced at
        # database level, not just serializer level.
        # Prevents duplicate logs for the same day.
        unique_together = ['user', 'date']

        # Most recent logs appear first.
        ordering = ['-date']

        # Index on user + date — the most common
        # query pattern: "get today's log for this user"
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f'{self.user.username} — {self.date}'


"""
Records what happened to each task during EOD review.
One record per task per daily log — enforced by
unique_together so no task can be reviewed twice
in the same EOD session.
Stores whether the task was completed and the user's
reason if it was not — Zoya uses reasons to give
honest, specific, empathetic feedback rather than
generic encouragement.
"""
class TaskCompletion(models.Model):

    # The daily log this completion record belongs to.
    # CASCADE — if log deleted, completions deleted too.
    # related_name allows daily_log.task_completions.all()
    daily_log = models.ForeignKey(
        DailyLog,
        on_delete=models.CASCADE,
        related_name='task_completions',
    )

    # Which task this record is about.
    # CASCADE — if task deleted, completion deleted too.
    # related_name allows task.completions.all()
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='completions',
    )

    # Did the user complete this task today?
    # Set during EOD review submission.
    # False by default — only marked True if user
    # explicitly confirms completion.
    completed = models.BooleanField(default=False)

    # If not completed — what reason did the user give?
    # Blank if task was completed.
    # Zoya reads this to give specific feedback:
    # "you mentioned you were tired — that's okay,
    # let's schedule this earlier tomorrow."
    reason_if_not = models.TextField(
        blank=True,
        default=''
    )

    # When this completion record was created.
    # Tells us what time the EOD review happened.
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One completion record per task per daily log.
        # Prevents duplicate EOD submissions for same task
        # within the same day's review session.
        unique_together = ['daily_log', 'task']

        # Most recent completion records first.
        ordering = ['-recorded_at']

    def __str__(self):
        status = 'done' if self.completed else 'not done'
        return (
            f'{self.daily_log.user.username} — '
            f'{self.task.title} — {status}'
        )