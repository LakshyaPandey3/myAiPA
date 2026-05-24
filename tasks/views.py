# tasks/views.py
# This file contains all task management views for myAiPA.
# Every view handles one specific task API endpoint.
# All endpoints are protected — valid JWT token required.
# Users can only see and modify their own tasks — never
# other users' tasks.
# Atomic transactions protect all write operations from
# race conditions in a concurrent environment.
# Pagination prevents large responses at world scale.
# User timezone used for date calculations — not server.

import pytz
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task
from .serializers import (
    TaskCreateSerializer,
    TaskSerializer,
    TaskSummarySerializer,
)


"""
Standard pagination for myAiPA task list endpoints.
Returns 20 tasks per page by default.
Client can request different page size up to 100.
Prevents large responses at scale.
"""
class TaskPagination(PageNumberPagination):
    # Default number of tasks per page.
    page_size = 20

    # Client can override page size using this param.
    # Example: /api/tasks/?page_size=50
    page_size_query_param = 'page_size'

    # Maximum page size allowed — prevents abuse.
    max_page_size = 100


"""
Handles listing all tasks and creating new tasks.
GET  /api/tasks/ — returns paginated non-deleted tasks
POST /api/tasks/ — creates a new task
Both require valid JWT token.
Users only see their own tasks — never others.
"""
class TaskListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return paginated non-deleted tasks for current user.
        Custom manager automatically excludes deleted tasks.
        Ordered by created_at descending by default.
        Supports ?page and ?page_size query parameters.
        """
        tasks = Task.objects.filter(
            user=request.user
        )

        # Apply pagination
        paginator = TaskPagination()
        paginated_tasks = paginator.paginate_queryset(
            tasks, request
        )

        serializer = TaskSerializer(
            paginated_tasks, many=True
        )

        return Response({
            'success': True,
            'count': tasks.count(),
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new task for current user.
        User is set from JWT token — never from request.
        Wrapped in atomic transaction — prevents partial
        saves if anything fails mid-operation.
        Returns complete task data on success.
        """
        serializer = TaskCreateSerializer(
            data=request.data
        )

        if serializer.is_valid():
            with transaction.atomic():
                # Pass user from JWT token — not from
                # request data. Prevents creating tasks
                # for other users.
                task = serializer.save(user=request.user)

            return Response({
                'success': True,
                'message': 'Task created successfully.',
                'data': TaskSerializer(task).data,
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'message': 'Failed to create task.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


"""
Handles retrieving, updating and deleting a single task.
GET    /api/tasks/{id}/ — get single task
PATCH  /api/tasks/{id}/ — update task partially
DELETE /api/tasks/{id}/ — soft delete task
All require valid JWT token.
Users can only access their own tasks.
"""
class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """
        Helper method to get a single task safely.
        Filters by both pk AND user — prevents users
        from accessing other users' tasks by guessing IDs.
        Custom manager excludes soft deleted tasks.
        Returns None if task not found or wrong user.
        This prevents task ID enumeration attacks —
        attacker cannot tell if task exists or belongs
        to someone else — both return 404.
        """
        try:
            return Task.objects.get(pk=pk, user=user)
        except Task.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        Return single task details for current user.
        Returns 404 if task not found or belongs
        to a different user — never reveals which.
        """
        task = self.get_object(pk, request.user)

        if not task:
            return Response({
                'success': False,
                'message': 'Task not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskSerializer(task)

        return Response({
            'success': True,
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Partially update a task for current user.
        Only sent fields are updated — others unchanged.
        Wrapped in atomic transaction — prevents race
        conditions when concurrent requests update
        the same task simultaneously.
        Returns updated task data on success.
        """
        task = self.get_object(pk, request.user)

        if not task:
            return Response({
                'success': False,
                'message': 'Task not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskCreateSerializer(
            instance=task,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            with transaction.atomic():
                updated_task = serializer.save()

            return Response({
                'success': True,
                'message': 'Task updated successfully.',
                'data': TaskSerializer(updated_task).data,
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Failed to update task.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Soft delete a task for current user.
        Sets is_deleted=True — never removes from database.
        EOD review can still see deleted tasks for
        accountability — Zoya asks why task was removed.
        Wrapped in atomic transaction — prevents partial
        state if save fails mid-operation.
        """
        task = self.get_object(pk, request.user)

        if not task:
            return Response({
                'success': False,
                'message': 'Task not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            task.is_deleted = True
            task.save()

        return Response({
            'success': True,
            'message': 'Task deleted successfully.',
        }, status=status.HTTP_200_OK)


"""
Returns tasks due today plus overdue tasks.
Used by dashboard and morning briefing to show
what the user needs to focus on right now.
Uses USER's timezone — not server timezone.
GET /api/tasks/today/
Requires valid JWT token.
"""
class TodayTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return all tasks due today and overdue tasks.
        TODAY is calculated in the USER's own timezone —
        not the server timezone. Critical for a global
        product used across different time zones.
        Overdue = due date past and not done.
        Today = due date is today regardless of status.
        Custom manager automatically excludes deleted tasks.
        """
        # Calculate today in USER's timezone — not server.
        # A user in India should see India's today,
        # not UTC today which could be a different date.
        try:
            user_tz = pytz.timezone(request.user.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fallback to UTC if user has invalid timezone.
            user_tz = pytz.UTC

        today = timezone.now().astimezone(user_tz).date()

        # Tasks due today — all statuses included
        # so user can see what they already completed today.
        today_tasks = Task.objects.filter(
            user=request.user,
            due_date=today,
        )

        # Overdue tasks — past due date and not done.
        # Excludes done tasks — no point showing completed
        # overdue tasks in the urgent list.
        overdue_tasks = Task.objects.filter(
            user=request.user,
            due_date__lt=today,
        ).exclude(status=Task.Status.DONE)

        today_serializer = TaskSummarySerializer(
            today_tasks, many=True
        )
        overdue_serializer = TaskSummarySerializer(
            overdue_tasks, many=True
        )

        return Response({
            'success': True,
            'data': {
                'today': today_serializer.data,
                'overdue': overdue_serializer.data,
                'today_count': len(today_serializer.data),
                'overdue_count': len(overdue_serializer.data),
            }
        }, status=status.HTTP_200_OK)


"""
Updates only the status of a single task.
Used when user clicks done/in-progress buttons.
Wrapped in atomic transaction for data integrity.
PATCH /api/tasks/{id}/status/
Requires valid JWT token.
"""
class TaskStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """
        Update only the status field of a task.
        Accepts: {"status": "done"} or
                 {"status": "in_progress"} or
                 {"status": "todo"}
        Strips status value — prevents whitespace errors.
        Validates against allowed choices before saving.
        Wrapped in atomic transaction — prevents race
        conditions on concurrent status updates.
        Model save() automatically manages completed_at.
        """
        try:
            task = Task.objects.get(
                pk=pk,
                user=request.user
            )
        except Task.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Task not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        # Strip whitespace — prevents "done " failing
        # valid status check due to trailing spaces.
        new_status = request.data.get('status', '').strip()

        # Get all valid status values from model choices.
        valid_statuses = [
            choice[0] for choice in Task.Status.choices
        ]

        if not new_status:
            return Response({
                'success': False,
                'message': 'Status field is required.',
                'errors': {
                    'status': ['This field is required.']
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in valid_statuses:
            return Response({
                'success': False,
                'message': 'Invalid status value.',
                'errors': {
                    'status': [
                        f'Status must be one of: '
                        f'{", ".join(valid_statuses)}'
                    ]
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            task.status = new_status
            # save() automatically sets or clears
            # completed_at based on new status value.
            task.save()

        return Response({
            'success': True,
            'message': f'Task marked as {new_status}.',
            'data': TaskSerializer(task).data,
        }, status=status.HTTP_200_OK)