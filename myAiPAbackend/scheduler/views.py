# scheduler/views.py
# This file contains all event management views for myAiPA.
# Every view handles one specific event API endpoint.
# All endpoints are protected — valid JWT token required.
# Users can only see and modify their own events — never
# other users' events.
# Conflict detection warns users about overlapping events
# without blocking creation — real schedules sometimes
# have overlaps and the user should decide.

import pytz
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event
from .serializers import (
    EventCreateSerializer,
    EventSerializer,
    EventSummarySerializer,
)


"""
Standard pagination for myAiPA event list endpoints.
Returns 20 events per page by default.
Client can request different page size up to 100.
Prevents large responses at scale.
"""
class EventPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def get_conflicting_events(user, start, end, exclude_id=None):
    """
    Find all events that overlap with the given
    start and end time for this user.
    exclude_id is used during updates to avoid
    an event conflicting with itself.
    Two events overlap if one starts before the
    other ends AND ends after the other starts.
    Returns a queryset of conflicting events.
    Caller is responsible for forcing evaluation
    (e.g. via list()) BEFORE creating a new event,
    otherwise lazy evaluation after creation would
    cause a new event to match itself.
    """
    conflicts = Event.objects.filter(
        user=user,
        start_datetime__lt=end,
        end_datetime__gt=start,
    )

    if exclude_id:
        conflicts = conflicts.exclude(pk=exclude_id)

    return conflicts


"""
Handles listing all events and creating new events.
GET  /api/events/ — returns paginated non-deleted events
POST /api/events/ — creates a new event, checks conflicts
Both require valid JWT token.
Users only see their own events — never others.
"""
class EventListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return paginated non-deleted events for current user.
        Custom manager automatically excludes deleted events.
        Ordered chronologically by start_datetime.
        Supports ?page and ?page_size query parameters.
        """
        events = Event.objects.filter(user=request.user)

        paginator = EventPagination()
        paginated_events = paginator.paginate_queryset(
            events, request
        )

        serializer = EventSerializer(
            paginated_events, many=True
        )

        return Response({
            'success': True,
            'count': events.count(),
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new event for current user.
        Checks for conflicts with existing events
        before saving — conflicts are returned as a
        warning, not a blocker. User decides whether
        to proceed with an overlapping event.
        Conflicts are forced into a list IMMEDIATELY,
        before the new event is created — otherwise the
        lazy queryset would evaluate after creation and
        the new event would incorrectly appear as its
        own conflict.
        Wrapped in atomic transaction.
        """
        serializer = EventCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():
            start = serializer.validated_data['start_datetime']
            end = serializer.validated_data['end_datetime']

            # Force immediate evaluation with list() —
            # runs the query NOW, before the new event
            # exists in the database. Prevents the new
            # event from matching itself as a conflict.
            conflicts = list(
                get_conflicting_events(
                    request.user, start, end
                )
            )

            with transaction.atomic():
                event = serializer.save(user=request.user)

            response_data = {
                'success': True,
                'message': 'Event created successfully.',
                'data': EventSerializer(event).data,
            }

            if conflicts:
                response_data['warning'] = (
                    'This event overlaps with '
                    'existing events.'
                )
                response_data['conflicts'] = (
                    EventSummarySerializer(
                        conflicts, many=True
                    ).data
                )

            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )

        return Response({
            'success': False,
            'message': 'Failed to create event.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


"""
Handles retrieving, updating and deleting a single event.
GET    /api/events/{id}/ — get single event
PATCH  /api/events/{id}/ — update event, checks conflicts
DELETE /api/events/{id}/ — soft delete event
All require valid JWT token.
Users can only access their own events.
"""
class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """
        Helper method to get a single event safely.
        Filters by both pk AND user — prevents IDOR
        attacks where a user guesses another user's
        event ID. Custom manager excludes deleted events.
        Returns None if not found or wrong user.
        """
        try:
            return Event.objects.get(pk=pk, user=user)
        except Event.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        Return single event details for current user.
        Returns 404 if not found or belongs to
        a different user — never reveals which.
        """
        event = self.get_object(pk, request.user)

        if not event:
            return Response({
                'success': False,
                'message': 'Event not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = EventSerializer(event)

        return Response({
            'success': True,
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Partially update an event for current user.
        Re-checks conflicts if start or end time changes.
        exclude_id=event.pk prevents the event from
        conflicting with its own previous state since
        the event already exists with a real pk before
        this filter runs.
        Wrapped in atomic transaction.
        """
        event = self.get_object(pk, request.user)

        if not event:
            return Response({
                'success': False,
                'message': 'Event not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = EventCreateSerializer(
            instance=event,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            start = serializer.validated_data.get(
                'start_datetime', event.start_datetime
            )
            end = serializer.validated_data.get(
                'end_datetime', event.end_datetime
            )

            conflicts = list(
                get_conflicting_events(
                    request.user,
                    start,
                    end,
                    exclude_id=event.pk
                )
            )

            with transaction.atomic():
                updated_event = serializer.save()

            response_data = {
                'success': True,
                'message': 'Event updated successfully.',
                'data': EventSerializer(updated_event).data,
            }

            if conflicts:
                response_data['warning'] = (
                    'This event overlaps with '
                    'existing events.'
                )
                response_data['conflicts'] = (
                    EventSummarySerializer(
                        conflicts, many=True
                    ).data
                )

            return Response(
                response_data, status=status.HTTP_200_OK
            )

        return Response({
            'success': False,
            'message': 'Failed to update event.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Soft delete an event for current user.
        Sets is_deleted=True — never removes from database.
        EOD review can still see deleted events for
        accountability.
        Wrapped in atomic transaction.
        """
        event = self.get_object(pk, request.user)

        if not event:
            return Response({
                'success': False,
                'message': 'Event not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            event.is_deleted = True
            event.save()

        return Response({
            'success': True,
            'message': 'Event deleted successfully.',
        }, status=status.HTTP_200_OK)


"""
Returns events happening today for current user.
Used by dashboard and morning briefing.
Uses USER's timezone — not server timezone.
GET /api/events/today/
Requires valid JWT token.
"""
class TodayEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all events happening today in the
        user's own timezone — not server timezone.
        An event counts as 'today' if it overlaps
        the user's local today window at all — covers
        events that start today, end today, span
        across today, or cross midnight.
        Falls back to UTC if user has an invalid
        or unrecognised timezone string.
        """
        try:
            user_tz = pytz.timezone(request.user.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            user_tz = pytz.UTC

        now_local = timezone.now().astimezone(user_tz)
        today_start = now_local.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = now_local.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Event overlaps today if it starts before today
        # ends AND ends after today begins.
        today_events = Event.objects.filter(
            user=request.user,
            start_datetime__lte=today_end,
            end_datetime__gte=today_start,
        )

        serializer = EventSummarySerializer(
            today_events, many=True
        )

        return Response({
            'success': True,
            'count': len(serializer.data),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)