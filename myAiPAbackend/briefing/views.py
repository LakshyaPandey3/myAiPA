# briefing/views.py
# This file contains all briefing views for myAiPA.
# Views are intentionally thin — all business logic
# lives in services.py. Each view does exactly three
# things: check authentication, call the right service
# function, return the response.

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyLog
from .serializers import (
    EODSubmissionSerializer,
    NextDayPlanSerializer,
)
from .services import (
    get_or_generate_morning_briefing,
    get_tasks_for_eod,
    save_next_day_plan,
    submit_eod_review,
)


"""
Standard pagination for myAiPA briefing history.
Returns 30 logs per page by default — one month.
Client can request up to 90 days at once.
"""
class BriefingPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 90


"""
Returns today's morning briefing for the current user.
If not yet generated — generates it now using Zoya.
If already generated today — returns cached version.
One AI call per user per day maximum.
GET /api/briefing/morning/
Requires valid JWT token.
"""
class MorningBriefingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return today's morning briefing.
        Calls service which handles generation and
        caching — view just passes the result through.
        """
        result = get_or_generate_morning_briefing(
            request.user
        )

        return Response({
            'success': True,
            'data': result,
        }, status=status.HTTP_200_OK)


"""
Returns today's tasks for the EOD review screen.
Shows tasks due today and overdue incomplete tasks.
Also returns whether EOD has already been submitted.
GET /api/briefing/eod/tasks/
Requires valid JWT token.
"""
class EODTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return tasks relevant for today's EOD review.
        View uses this to build the accountability
        screen before the user submits their review.
        """
        result = get_tasks_for_eod(request.user)

        return Response({
            'success': True,
            'data': result,
        }, status=status.HTTP_200_OK)


"""
Processes the user's EOD review submission.
Validates completion data, creates TaskCompletion
records, generates Zoya's summary and score.
All writes wrapped in atomic transaction.
POST /api/briefing/eod/submit/
Requires valid JWT token.
"""
class EODSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Submit today's EOD review.
        Validates incoming data through serializer
        before passing to service for processing.
        Blocked if EOD already submitted today.
        """
        serializer = EODSubmissionSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid EOD submission data.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        result = submit_eod_review(
            user=request.user,
            completions_data=serializer.validated_data[
                'completions'
            ],
        )

        if result.get('error'):
            return Response({
                'success': False,
                'message': result['message'],
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'message': (
                'EOD review submitted successfully. '
                'Great work reflecting on your day!'
            ),
            'data': result,
        }, status=status.HTTP_200_OK)


"""
Saves the user's next day plan and returns Zoya's
warm closing message for the night.
Validates goals structure and intention before saving.
All writes wrapped in atomic transaction.
POST /api/briefing/nextday/
Requires valid JWT token.
"""
class NextDayPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Save tomorrow's goals and intention.
        Validates that goals have correct structure
        (each with goal text and priority) and that
        intention is a clean non-empty sentence.
        Generates Zoya's closing message for the night.
        """
        serializer = NextDayPlanSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid next day plan data.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        result = save_next_day_plan(
            user=request.user,
            goals=serializer.validated_data['goals'],
            intention=serializer.validated_data['intention'],
        )

        return Response({
            'success': True,
            'message': (
                'Your plan for tomorrow has been saved. '
                'Rest well!'
            ),
            'data': result,
        }, status=status.HTTP_200_OK)


"""
Returns paginated history of daily logs for the user.
Shows briefings, EOD summaries, scores and goals.
Most recent logs appear first.
GET /api/briefing/history/
Requires valid JWT token.
"""
class BriefingHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Return paginated history of daily logs.
        Each log contains morning briefing text,
        EOD summary, productivity score, and goals.
        Supports ?page and ?page_size query parameters.
        Default 30 per page, maximum 90.
        """
        logs = DailyLog.objects.filter(
            user=request.user
        ).order_by('-date')

        paginator = BriefingPagination()
        paginated_logs = paginator.paginate_queryset(
            logs, request
        )

        history = [
            {
                'date': str(log.date),
                'morning_briefing': log.morning_briefing,
                'eod_summary': log.eod_summary,
                'productivity_score': log.productivity_score,
                'next_day_goals': log.next_day_goals,
                'next_day_intention': log.next_day_intention,
                'eod_submitted': log.eod_submitted,
            }
            for log in paginated_logs
        ]

        return Response({
            'success': True,
            'count': logs.count(),
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'data': history,
        }, status=status.HTTP_200_OK)