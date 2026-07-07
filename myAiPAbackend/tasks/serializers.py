# tasks/serializers.py
# This file handles all data validation and conversion
# for myAiPA's task management system.
# Every piece of task data coming in or going out
# passes through these serializers first.

import re

from rest_framework import serializers

from .models import Task


"""
Full task serializer for myAiPA.
Used when displaying complete task details to React.
Returns all task fields needed for the task list
screen, task detail view, and dashboard display.
All fields are read only — this serializer is
purely for display, never for creating or updating.
User field intentionally excluded — React already
knows who is logged in from the JWT token.
"""
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'is_deleted',
            'created_at',
            'updated_at',
        ]

        # ALL fields read only — TaskSerializer is
        # for display only. TaskCreateSerializer
        # handles all create and update operations.
        # This prevents accidental writes through
        # this serializer in any view.
        read_only_fields = [
            'id',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'is_deleted',
            'created_at',
            'updated_at',
        ]


"""
Task creation and update serializer for myAiPA.
Used for both creating new tasks and updating
existing ones — partial=True handles updates.
Validates all incoming task data thoroughly.
Protects against HTML injection in text fields.
User is never accepted from request data —
always set from JWT token in the view.
"""
class TaskCreateSerializer(serializers.ModelSerializer):

    # Title is required — every task must have one.
    # max_length matches model field.
    # HTML injection protection in validate_title.
    title = serializers.CharField(
        required=True,
        max_length=255,
    )

    # Description is optional — user can skip it.
    # max_length=2000 prevents extremely large inputs.
    # allow_blank=True so empty string is accepted.
    description = serializers.CharField(
        required=False,
        default='',
        max_length=2000,
        allow_blank=True,
    )

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'priority',
            'due_date',
            'status',
        ]

    def validate_title(self, value):
        """
        Strip whitespace from task title.
        Reject HTML tags — prevents XSS attacks
        when React displays the title on screen.
        Ensure title is not empty after stripping.
        """
        # Normalize ALL whitespace — not just strip.
        # Handles spaces, tabs, newlines, multiple spaces.
        value = ' '.join(value.split())

        # Reject HTML angle brackets — XSS protection.
        # Task titles must be plain text only.
        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Task title cannot contain HTML characters."
            )

        if len(value) < 1:
            raise serializers.ValidationError(
                "Task title cannot be empty."
            )

        return value

    def validate_description(self, value):
        """
        Strip whitespace from task description.
        Reject HTML tags — prevents XSS attacks
        when React displays description on screen.
        Empty description is allowed.
        """
        value = value.strip()

        # Reject HTML angle brackets — XSS protection.
        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Task description cannot contain "
                "HTML characters."
            )

        return value

    def create(self, validated_data):
        """
        Create and return a new myAiPA task.
        User is passed from the view via save(user=...)
        and merged into validated_data by DRF automatically.
        This prevents users from creating tasks
        for other users by sending a different user id.
        """
        return Task.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return existing myAiPA task.
        Only updates fields that were actually sent —
        leaves everything else completely unchanged.
        This is a partial update — not a full replace.
        completed_at is managed by model save() —
        automatically set when status changes to done.
        """
        instance.title = validated_data.get(
            'title',
            instance.title
        )
        instance.description = validated_data.get(
            'description',
            instance.description
        )
        instance.priority = validated_data.get(
            'priority',
            instance.priority
        )
        instance.due_date = validated_data.get(
            'due_date',
            instance.due_date
        )
        instance.status = validated_data.get(
            'status',
            instance.status
        )
        # save() automatically manages completed_at
        # based on the new status value.
        instance.save()
        return instance


"""
Lightweight task serializer for myAiPA briefings.
Used by morning briefing and EOD review to display
a summary of tasks without all the heavy detail fields.
Keeps API responses fast when showing many tasks.
All fields read only — summary is display only.
No updates happen through this serializer.
"""
class TaskSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'is_deleted',
        ]

        # All fields read only — summary is display only.
        # No updates happen through this serializer.
        read_only_fields = [
            'id',
            'title',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'is_deleted',
        ]