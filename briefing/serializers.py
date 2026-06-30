# briefing/serializers.py
# This file handles input validation for myAiPA's
# briefing system endpoints.
# Two serializers — one for EOD review submission,
# one for next day planning.
# Neither is a ModelSerializer — they validate
# incoming request data, not model instances.

import re

from rest_framework import serializers


"""
Validates a single task completion record submitted
during EOD review. Used as a nested serializer inside
EODSubmissionSerializer to validate each item in the
completions list individually.
"""
class TaskCompletionItemSerializer(serializers.Serializer):

    # Which task this completion record is for.
    # Must be a positive integer — task IDs are always
    # positive. View verifies the task belongs to the
    # current user before processing.
    task_id = serializers.IntegerField(
        required=True,
        min_value=1,
    )

    # Did the user complete this task?
    # Required — user must explicitly say yes or no.
    completed = serializers.BooleanField(
        required=True,
    )

    # Reason if not completed — optional.
    # Only meaningful when completed=False.
    # Zoya reads this to give specific empathetic
    # feedback rather than generic responses.
    reason_if_not = serializers.CharField(
        required=False,
        default='',
        max_length=1000,
        allow_blank=True,
    )

    def validate_reason_if_not(self, value):
        """
        Strip whitespace from reason.
        Reject HTML tags — prevents XSS attacks
        when Zoya's response references the reason.
        """
        value = value.strip()

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Reason cannot contain HTML characters."
            )

        return value


"""
Validates the complete EOD review submission.
Wraps a list of TaskCompletionItemSerializer —
one item per task being reviewed.
Rejects empty submissions and malformed data.
"""
class EODSubmissionSerializer(serializers.Serializer):

    # List of task completion records.
    # many=True means each item is validated by
    # TaskCompletionItemSerializer individually.
    completions = serializers.ListField(
        child=TaskCompletionItemSerializer(),
        required=True,
        min_length=1,
    )

    def validate_completions(self, value):
        """
        Ensure no duplicate task_ids in the submission.
        A user cannot submit two different completion
        records for the same task in one EOD review.
        """
        task_ids = [item['task_id'] for item in value]
        if len(task_ids) != len(set(task_ids)):
            raise serializers.ValidationError(
                "Duplicate task IDs found in submission. "
                "Each task can only be reviewed once."
            )
        return value


"""
Validates a single goal item in the next day plan.
Each goal must have both a goal text and a priority.
Used as a nested serializer inside NextDayPlanSerializer.
"""
class GoalItemSerializer(serializers.Serializer):

    # The goal text — what the user wants to accomplish.
    # Required, non-empty, HTML-protected.
    goal = serializers.CharField(
        required=True,
        max_length=500,
    )

    # Priority of this goal — must be one of three
    # values only. Zoya uses this to highlight the
    # most important goal in the morning briefing.
    priority = serializers.ChoiceField(
        choices=['high', 'medium', 'low'],
        required=True,
    )

    def validate_goal(self, value):
        """
        Normalize whitespace in goal text.
        Reject HTML tags — prevents XSS attacks.
        Ensure goal is not empty after normalizing.
        """
        value = ' '.join(value.split())

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Goal cannot contain HTML characters."
            )

        if len(value) < 1:
            raise serializers.ValidationError(
                "Goal cannot be empty."
            )

        return value


"""
Validates the complete next day plan submission.
Ensures goals list has 1-3 properly structured items
and intention is a clean non-empty sentence.
"""
class NextDayPlanSerializer(serializers.Serializer):

    # List of goals for tomorrow — minimum 1, maximum 3.
    # We said "top 3 goals" — no more, no less than 1.
    # Each item validated by GoalItemSerializer.
    goals = serializers.ListField(
        child=GoalItemSerializer(),
        required=True,
        min_length=1,
        max_length=3,
    )

    # One sentence describing how the user wants to
    # feel at the end of tomorrow.
    # Surfaced in next morning's briefing by Zoya.
    intention = serializers.CharField(
        required=True,
        max_length=500,
    )

    def validate_intention(self, value):
        """
        Normalize whitespace in intention.
        Reject HTML tags — prevents XSS attacks.
        Ensure intention is not empty after normalizing.
        """
        value = ' '.join(value.split())

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Intention cannot contain HTML characters."
            )

        if len(value) < 1:
            raise serializers.ValidationError(
                "Intention cannot be empty."
            )

        return value

    def validate_goals(self, value):
        """
        Ensure no duplicate goal texts in the plan.
        A user should not set the same goal twice
        with different priorities — that's a mistake.
        """
        goal_texts = [
            item['goal'].lower() for item in value
        ]
        if len(goal_texts) != len(set(goal_texts)):
            raise serializers.ValidationError(
                "Duplicate goals found. "
                "Each goal must be unique."
            )
        return value