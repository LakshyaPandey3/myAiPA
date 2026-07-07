# scheduler/serializers.py
# This file handles all data validation and conversion
# for myAiPA's event scheduling system.
# Every piece of event data coming in or going out
# passes through these serializers first.

import re

from rest_framework import serializers

from .models import Event


"""
Full event serializer for myAiPA.
Used when displaying complete event details to React.
All fields read only — this serializer is purely for
display, never for creating or updating.
User field intentionally excluded — React already
knows who is logged in from the JWT token.
"""
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'description',
            'start_datetime',
            'end_datetime',
            'location',
            'is_all_day',
            'is_recurring',
            'recurrence_rule',
            'is_deleted',
            'created_at',
            'updated_at',
        ]

        # ALL fields read only — EventSerializer is
        # for display only. EventCreateSerializer
        # handles all create and update operations.
        # Prevents accidental writes through this
        # serializer in any view.
        read_only_fields = [
            'id',
            'title',
            'description',
            'start_datetime',
            'end_datetime',
            'location',
            'is_all_day',
            'is_recurring',
            'recurrence_rule',
            'is_deleted',
            'created_at',
            'updated_at',
        ]


"""
Event creation and update serializer for myAiPA.
Used for both creating new events and updating
existing ones — partial=True handles updates.
Validates all incoming event data thoroughly.
Protects against HTML injection in text fields.
Ensures end_datetime is always after start_datetime.
Ensures recurrence_rule and is_recurring stay
logically consistent with each other.
User is never accepted from request data —
always set from JWT token in the view.
"""
class EventCreateSerializer(serializers.ModelSerializer):

    # Title is required — every event must have one.
    # max_length matches model field.
    # HTML injection protection in validate_title.
    title = serializers.CharField(
        required=True,
        max_length=255,
    )

    # Description is optional — user can skip it.
    # max_length=2000 prevents extremely large inputs.
    description = serializers.CharField(
        required=False,
        default='',
        max_length=2000,
        allow_blank=True,
    )

    # Location is optional.
    # max_length=255 matches model field.
    location = serializers.CharField(
        required=False,
        default='',
        max_length=255,
        allow_blank=True,
    )

    # Recurrence rule is optional — only meaningful
    # when is_recurring=True. Consistency enforced
    # in validate() below.
    recurrence_rule = serializers.CharField(
        required=False,
        default='',
        max_length=100,
        allow_blank=True,
    )

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'start_datetime',
            'end_datetime',
            'location',
            'is_all_day',
            'is_recurring',
            'recurrence_rule',
        ]

    def validate_title(self, value):
        """
        Normalize ALL whitespace in event title.
        Collapses multiple spaces, removes internal
        newlines and tabs — titles must be clean
        single line plain text only.
        Reject HTML tags — prevents XSS attacks
        when React displays the title on screen.
        Ensure title is not empty after normalizing.
        """
        value = ' '.join(value.split())

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Event title cannot contain HTML characters."
            )

        if len(value) < 1:
            raise serializers.ValidationError(
                "Event title cannot be empty."
            )

        return value

    def validate_description(self, value):
        """
        Strip whitespace from description.
        Reject HTML tags — prevents XSS attacks
        when React displays description on screen.
        Empty description is allowed.
        """
        value = value.strip()

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Event description cannot contain "
                "HTML characters."
            )

        return value

    def validate_location(self, value):
        """
        Strip whitespace from location.
        Reject HTML tags — prevents XSS attacks.
        Empty location is allowed.
        """
        value = value.strip()

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Event location cannot contain "
                "HTML characters."
            )

        return value

    def validate_recurrence_rule(self, value):
        """
        Strip whitespace from recurrence rule.
        Reject HTML tags — prevents XSS attacks.
        Full consistency check with is_recurring
        happens in validate() below — this method
        only handles individual field cleanliness.
        """
        value = value.strip()

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "Recurrence rule cannot contain "
                "HTML characters."
            )

        return value

    def validate(self, attrs):
        """
        Cross field validation for events.
        1. Ensures end_datetime is always after
           start_datetime — prevents events that
           end before they start.
        2. Ensures recurrence_rule is provided when
           is_recurring=True — Zoya needs to know HOW
           often an event repeats, not just that it does.
        3. Auto-clears recurrence_rule when
           is_recurring=False — prevents stale,
           inconsistent data in the database.
        On partial update, falls back to instance
        values for any field not included in
        this specific request.
        """
        start = attrs.get(
            'start_datetime',
            getattr(self.instance, 'start_datetime', None)
        )
        end = attrs.get(
            'end_datetime',
            getattr(self.instance, 'end_datetime', None)
        )

        if start and end and end <= start:
            raise serializers.ValidationError({
                'end_datetime': (
                    'End time must be after start time.'
                )
            })

        # Check recurring event consistency.
        is_recurring = attrs.get(
            'is_recurring',
            getattr(self.instance, 'is_recurring', False)
        )
        recurrence_rule = attrs.get(
            'recurrence_rule',
            getattr(self.instance, 'recurrence_rule', '')
        )

        if is_recurring and not recurrence_rule.strip():
            raise serializers.ValidationError({
                'recurrence_rule': (
                    'Recurrence rule is required when '
                    'the event is marked as recurring.'
                )
            })

        if not is_recurring and recurrence_rule.strip():
            # Auto-clear recurrence_rule if is_recurring
            # is False — prevents stale data, does not
            # error out, just silently cleans it up.
            attrs['recurrence_rule'] = ''

        return attrs

    def create(self, validated_data):
        """
        Create and return a new myAiPA event.
        User is passed from the view via save(user=...)
        and merged into validated_data by DRF automatically.
        This prevents users from creating events
        for other users by sending a different user id.
        """
        return Event.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return existing myAiPA event.
        Only updates fields that were actually sent —
        leaves everything else completely unchanged.
        This is a partial update — not a full replace.
        """
        instance.title = validated_data.get(
            'title', instance.title
        )
        instance.description = validated_data.get(
            'description', instance.description
        )
        instance.start_datetime = validated_data.get(
            'start_datetime', instance.start_datetime
        )
        instance.end_datetime = validated_data.get(
            'end_datetime', instance.end_datetime
        )
        instance.location = validated_data.get(
            'location', instance.location
        )
        instance.is_all_day = validated_data.get(
            'is_all_day', instance.is_all_day
        )
        instance.is_recurring = validated_data.get(
            'is_recurring', instance.is_recurring
        )
        instance.recurrence_rule = validated_data.get(
            'recurrence_rule', instance.recurrence_rule
        )
        instance.save()
        return instance


"""
Lightweight event serializer for myAiPA briefings.
Used by morning briefing and EOD review to display
a summary of events without all the heavy detail fields.
Keeps API responses fast when showing many events.
All fields read only — summary is display only.
No updates happen through this serializer.
"""
class EventSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'start_datetime',
            'end_datetime',
            'is_all_day',
            'is_deleted',
        ]

        read_only_fields = [
            'id',
            'title',
            'start_datetime',
            'end_datetime',
            'is_all_day',
            'is_deleted',
        ]