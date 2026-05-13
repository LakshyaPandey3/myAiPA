# accounts/models.py
# This file defines the User model for myAiPA.
# We extend Django's built-in AbstractUser so we get
# all standard auth features (login, password hashing,
# permissions) plus our own custom fields on top.

from django.contrib.auth.models import AbstractUser
from django.db import models

"""
 Custom User model for myAiPA.
 Extends Django's AbstractUser to add myAiPA-specific
 fields. This model is the foundation of the entire
 application — every task, event, and briefing
 belongs to a User.
 """
class User(AbstractUser):
 
    # The user's local timezone.
    # Used by Celery to send the myAiPA morning briefing
    # at the correct local time (default: India).
    timezone = models.CharField(
        max_length=50,
        default='Asia/Kolkata'
    )

    # The name the user gives their myAiPA assistant.
    # Used to personalise greetings — "Good morning
    # from Aria!" feels warmer than "Good morning
    # from Assistant!"
    myAiPA_name = models.CharField(
        max_length=50,
        default='Zoya'
    )

    # The time the user wants their myAiPA morning
    # briefing delivered. Stored as HH:MM:SS.
    # Celery reads this to know exactly when to
    # generate and send the briefing.
    briefing_time = models.TimeField(
        default='07:00:00'
    )

    # Tracks how many consecutive days the user has
    # completed their EOD review inside myAiPA.
    # Like Duolingo streaks. myAiPA celebrates
    # milestones — "7 days in a row! You are on fire!"
    streak_count = models.IntegerField(
        default=0
    )

    # Automatically records when the user registered
    # with myAiPA. auto_now_add=True means Django sets
    # this once when the record is created and never
    # changes it again.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        # When Django needs to display this user as
        # text (e.g. in myAiPA admin panel), show their
        # email instead of "User object (1)"
        return self.email