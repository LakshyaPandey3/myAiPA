# briefing/services.py
# This file contains all business logic for myAiPA's
# briefing system. Views are thin — all real work
# happens here. This separation means logic can be
# tested independently of HTTP requests.

from datetime import timedelta

import pytz
from django.db import transaction
from django.utils import timezone

from ai_service.client import get_ai_response
from ai_service.prompts import (
    EOD_REVIEW_PROMPT,
    MORNING_BRIEFING_PROMPT,
    NEXT_DAY_PLAN_PROMPT,
    get_personality,
)
from scheduler.models import Event
from tasks.models import Task

from .models import DailyLog, TaskCompletion


def _get_user_today(user):
    """
    Returns today's date in the user's own timezone.
    Never uses server timezone — a user in India should
    get India's today, not UTC today which could be
    a completely different date.
    Falls back to UTC if user has invalid timezone.
    """
    try:
        user_tz = pytz.timezone(user.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        user_tz = pytz.UTC

    return timezone.now().astimezone(user_tz).date()


def _get_user_tz(user):
    """
    Returns the user's pytz timezone object.
    Extracted as a helper to avoid repeating the
    same try/except block across multiple functions.
    Falls back to UTC if user has invalid timezone.
    """
    try:
        return pytz.timezone(user.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        return pytz.UTC


def _get_yesterday_intention(user, today):
    """
    Safely fetches yesterday's next_day_intention.
    Returns empty string if no log exists for yesterday
    — handles first time users and users who skipped
    next day planning the previous evening.
    Zoya uses this to open the morning briefing with
    a personal reference to what the user said last night.
    """
    yesterday = today - timedelta(days=1)

    try:
        yesterday_log = DailyLog.objects.get(
            user=user,
            date=yesterday,
        )
        return yesterday_log.next_day_intention or ''
    except DailyLog.DoesNotExist:
        return ''


def _get_yesterday_top_priority_goal(user, today):
    """
    Safely fetches the highest priority goal from
    yesterday's next day planning.
    Returns empty string if no log or no goals exist.
    Used in morning briefing so Zoya can reference
    what the user planned as their top priority.
    Priority order: high > medium > low.
    """
    yesterday = today - timedelta(days=1)

    try:
        yesterday_log = DailyLog.objects.get(
            user=user,
            date=yesterday,
        )
        goals = yesterday_log.next_day_goals

        if not goals:
            return ''

        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_goals = sorted(
            goals,
            key=lambda g: priority_order.get(
                g.get('priority', 'low'), 2
            )
        )
        return (
            sorted_goals[0].get('goal', '')
            if sorted_goals else ''
        )

    except DailyLog.DoesNotExist:
        return ''


def _parse_eod_response(ai_response: str):
    """
    Parses Zoya's EOD review response into summary
    and productivity score.
    Expected format from AI:
    SUMMARY: [4-6 sentence summary]
    SCORE: [number 1-10]

    Handles malformed responses gracefully — if the
    AI does not follow the format exactly, we extract
    what we can and default score to None rather than
    crashing the entire EOD submission.
    Score is clamped to 1-10 range even if AI returns
    a number outside that range.
    """
    summary = ai_response
    score = None

    try:
        if 'SCORE:' in ai_response:
            parts = ai_response.split('SCORE:')
            summary_part = parts[0]
            score_part = parts[1].strip()

            if 'SUMMARY:' in summary_part:
                summary = summary_part.split(
                    'SUMMARY:'
                )[1].strip()
            else:
                summary = summary_part.strip()

            score_digits = ''.join(
                filter(str.isdigit, score_part.split()[0])
            )
            if score_digits:
                parsed_score = int(score_digits)
                if 1 <= parsed_score <= 10:
                    score = parsed_score

    except Exception:
        summary = ai_response
        score = None

    return summary.strip(), score


def get_or_generate_morning_briefing(user):
    """
    Returns today's morning briefing for the user.
    If briefing already generated today — returns
    cached version immediately without calling AI.
    If not yet generated — gathers all context,
    calls Zoya, saves result, returns it.
    One AI call per user per day maximum.
    """
    today = _get_user_today(user)
    user_tz = _get_user_tz(user)

    daily_log, created = DailyLog.objects.get_or_create(
        user=user,
        date=today,
    )

    if daily_log.morning_briefing_generated:
        return {
            'briefing': daily_log.morning_briefing,
            'date': str(today),
            'already_generated': True,
        }

    today_tasks = Task.objects.filter(
        user=user,
        due_date=today,
    )

    overdue_tasks = Task.objects.filter(
        user=user,
        due_date__lt=today,
    ).exclude(status=Task.Status.DONE)

    now_local = timezone.now().astimezone(user_tz)
    today_start = now_local.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_end = now_local.replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    today_events = Event.objects.filter(
        user=user,
        start_datetime__lte=today_end,
        end_datetime__gte=today_start,
    )

    yesterday_intention = _get_yesterday_intention(
        user, today
    )
    top_priority_goal = _get_yesterday_top_priority_goal(
        user, today
    )

    tasks_text = '\n'.join([
        f'- {t.title} (priority: {t.priority})'
        for t in today_tasks
    ]) or 'No tasks scheduled for today.'

    overdue_text = '\n'.join([
        f'- {t.title} (due: {t.due_date})'
        for t in overdue_tasks
    ]) or 'No overdue tasks.'

    events_text = '\n'.join([
        f'- {e.title} at '
        f'{e.start_datetime.astimezone(user_tz).strftime("%I:%M %p")}'
        for e in today_events
    ]) or 'No events scheduled for today.'

    # PHASE 1 — Build prompt from database data.
    # All DB reads complete before AI call.
    personality = get_personality(user.myAiPA_name)
    prompt = MORNING_BRIEFING_PROMPT.format(
        personality=personality,
        today=str(today),
        user_name=user.username,
        yesterday_intention=yesterday_intention or 'None set.',
        top_priority_goal=top_priority_goal or 'None set.',
        tasks=tasks_text,
        events=events_text,
        overdue_tasks=overdue_text,
    )

    # PHASE 2 — Call AI outside any transaction.
    briefing_text = get_ai_response(prompt)

    # PHASE 3 — Save result in short transaction.
    with transaction.atomic():
        daily_log.morning_briefing = briefing_text
        daily_log.morning_briefing_generated = True
        daily_log.save()

    return {
        'briefing': briefing_text,
        'date': str(today),
        'already_generated': False,
    }


def get_tasks_for_eod(user):
    """
    Returns the tasks relevant for today's EOD review.
    Includes today's tasks and overdue incomplete tasks —
    only tasks the user was actually responsible for
    today. Not all tasks ever created.
    Also returns whether EOD has already been submitted
    today — view uses this to block duplicate submissions.
    """
    today = _get_user_today(user)

    try:
        daily_log = DailyLog.objects.get(
            user=user, date=today
        )
        if daily_log.eod_submitted:
            return {
                'already_submitted': True,
                'today': [],
                'overdue': [],
                'today_count': 0,
                'overdue_count': 0,
            }
    except DailyLog.DoesNotExist:
        pass

    today_tasks = Task.objects.filter(
        user=user,
        due_date=today,
    )

    overdue_tasks = Task.objects.filter(
        user=user,
        due_date__lt=today,
    ).exclude(status=Task.Status.DONE)

    today_list = [
        {
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'status': t.status,
            'due_date': str(t.due_date),
        }
        for t in today_tasks
    ]

    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'status': t.status,
            'due_date': str(t.due_date),
        }
        for t in overdue_tasks
    ]

    return {
        'already_submitted': False,
        'today': today_list,
        'overdue': overdue_list,
        'today_count': today_tasks.count(),
        'overdue_count': overdue_tasks.count(),
    }


def submit_eod_review(user, completions_data):
    """
    Processes the user's EOD review submission.
    completions_data is a list of dicts:
    [
        {
            "task_id": 1,
            "completed": true,
            "reason_if_not": ""
        },
        {
            "task_id": 2,
            "completed": false,
            "reason_if_not": "Was too tired after work"
        }
    ]
    Phase 1 — creates TaskCompletion records in a
    transaction. Phase 2 — calls Groq AI outside the
    transaction (never hold DB connection during network
    calls). Phase 3 — saves AI results in a second
    transaction. This pattern prevents connection pool
    exhaustion at scale.
    """
    today = _get_user_today(user)

    daily_log, created = DailyLog.objects.get_or_create(
        user=user,
        date=today,
    )

    if daily_log.eod_submitted:
        return {
            'error': True,
            'message': (
                'You have already submitted your EOD '
                'review for today. See you tomorrow!'
            ),
        }

    completed_tasks = []
    incomplete_tasks = []

    # PHASE 1 — Save TaskCompletion records.
    # Keep this transaction short — no network calls.
    with transaction.atomic():
        for item in completions_data:
            task_id = item.get('task_id')
            completed = item.get('completed', False)
            reason = item.get('reason_if_not', '').strip()

            try:
                task = Task.objects.get(
                    pk=task_id, user=user
                )
            except Task.DoesNotExist:
                continue

            TaskCompletion.objects.get_or_create(
                daily_log=daily_log,
                task=task,
                defaults={
                    'completed': completed,
                    'reason_if_not': reason,
                }
            )

            if completed:
                completed_tasks.append(task.title)
            else:
                incomplete_tasks.append({
                    'title': task.title,
                    'reason': reason or 'No reason given.',
                })

    # Get deleted tasks — outside transaction is fine,
    # this is a read-only query.
    today_deleted = Task.objects.deleted_only().filter(
        user=user,
        due_date=today,
    )
    deleted_titles = [t.title for t in today_deleted]

    # Format all task data as readable text for prompt
    completed_text = '\n'.join([
        f'- {t}' for t in completed_tasks
    ]) or 'None completed.'

    incomplete_text = '\n'.join([
        f'- {item["title"]}: {item["reason"]}'
        for item in incomplete_tasks
    ]) or 'All tasks completed.'

    deleted_text = '\n'.join([
        f'- {t}' for t in deleted_titles
    ]) or 'None deleted.'

    # PHASE 2 — Call Groq AI OUTSIDE transaction.
    # Never hold a DB connection during a network call.
    # If AI fails — TaskCompletion records already saved,
    # we just won't have a summary. Handled gracefully.
    personality = get_personality(user.myAiPA_name)
    prompt = EOD_REVIEW_PROMPT.format(
        personality=personality,
        today=str(today),
        user_name=user.username,
        completed_tasks=completed_text,
        incomplete_tasks=incomplete_text,
        deleted_tasks=deleted_text,
    )

    ai_response = get_ai_response(prompt)
    summary, score = _parse_eod_response(ai_response)

    # PHASE 3 — Save AI results in a second transaction.
    # Short transaction — just updating DailyLog fields.
    with transaction.atomic():
        daily_log.eod_summary = summary
        daily_log.productivity_score = score
        daily_log.eod_submitted = True
        daily_log.save()

    return {
        'error': False,
        'summary': summary,
        'productivity_score': score,
        'date': str(today),
    }

def save_next_day_plan(user, goals, intention):
    """
    Saves the user's next day plan and generates
    Zoya's warm closing message for the night.
    goals is a list of dicts with goal and priority:
    [
        {"goal": "finish project", "priority": "high"},
        {"goal": "call dentist", "priority": "medium"},
        {"goal": "gym", "priority": "low"}
    ]
    intention is a single sentence string describing
    how the user wants to feel at the end of tomorrow.
    All database writes wrapped in atomic transaction.
    """
    today = _get_user_today(user)
    tomorrow = today + timedelta(days=1)

    daily_log, created = DailyLog.objects.get_or_create(
        user=user,
        date=today,
    )

    with transaction.atomic():
        daily_log.next_day_goals = goals
        daily_log.next_day_intention = intention.strip()
        daily_log.save()

    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    sorted_goals = sorted(
        goals,
        key=lambda g: priority_order.get(
            g.get('priority', 'low'), 2
        )
    )

    goals_text = '\n'.join([
        f'- [{g.get("priority", "medium").upper()}] '
        f'{g.get("goal", "")}'
        for g in sorted_goals
    ]) or 'No goals set.'

    personality = get_personality(user.myAiPA_name)
    prompt = NEXT_DAY_PLAN_PROMPT.format(
        personality=personality,
        user_name=user.username,
        tomorrow=str(tomorrow),
        goals=goals_text,
        intention=intention.strip() or 'None set.',
    )

    closing_message = get_ai_response(prompt)

    return {
        'closing_message': closing_message,
        'goals_saved': len(goals),
        'intention_saved': bool(intention.strip()),
        'date': str(today),
        'tomorrow': str(tomorrow),
    }