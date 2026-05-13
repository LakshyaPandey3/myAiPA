# accounts/admin.py
# This file registers myAiPA's User model with Django's
# admin panel so we can view and manage all users
# directly from the browser without touching the database.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

"""
Custom admin configuration for myAiPA's User model.
Extends Django's built-in UserAdmin to include
myAiPA-specific fields and a clean, organised
admin interface for managing all myAiPA users.
"""
@admin.register(User)
class CustomUserAdmin(UserAdmin):


    # Columns shown in the users list view.
    # Ordered from most important to least important.
    # These tell us everything we need to know about
    # a user at a single glance.
    list_display = (
        'email',          # primary identifier
        'username',       # secondary identifier
        'myAiPA_name',    # their Zoya's name
        'timezone',       # for briefing timing
        'briefing_time',  # when they get briefing
        'streak_count',   # engagement indicator
        'is_active',      # account status
        'is_staff',       # admin or regular user
        'last_login',     # last seen in myAiPA
        'created_at',     # when they joined myAiPA
    )

    # Filter buttons on the right side of admin panel.
    # Lets us segment users by important categories
    # instantly without writing any database queries.
    list_filter = (
        'is_staff',       # admins vs regular users
        'is_active',      # active vs inactive accounts
        'timezone',       # users by timezone
    )

    # Search box at the top of the admin panel.
    # Lets us find any specific myAiPA user instantly
    # by typing their email, username or assistant name.
    search_fields = (
        'email',
        'username',
        'myAiPA_name',
    )

    # Default sorting — newest myAiPA users appear first.
    # The minus sign means descending order.
    # Most useful when reviewing new signups.
    ordering = ('-created_at',)

    # Read only fields cannot be edited from admin panel.
    # created_at should never be manually changed —
    # it is automatically set when user registers.
    readonly_fields = ('created_at', 'last_login')

    # Show 25 users per page for clean readability.
    # 100 (Django default) is too many to scan at once.
    list_per_page = 25

    # Date navigation bar at top of admin list.
    # Browse myAiPA users by their registration date —
    # year → month → day.
    date_hierarchy = 'created_at'

    # fieldsets controls the layout of the user
    # detail page in the admin panel.
    # We take all of Django's default sections and
    # add our own myAiPA Settings section at the bottom.
    fieldsets = UserAdmin.fieldsets + (
        ('myAiPA Settings', {
            'description': (
                'These settings control how myAiPA '
                'personalises the experience for this user.'
            ),
            'fields': (
                'myAiPA_name',
                'timezone',
                'briefing_time',
                'streak_count',
                'created_at',
            )
        }),
    )

    # add_fieldsets controls the layout when creating
    # a brand new user from the admin panel.
    # We add myAiPA fields to the creation form too.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('myAiPA Settings', {
            'fields': (
                'email',
                'myAiPA_name',
                'timezone',
                'briefing_time',
            )
        }),
    )

    """
    Override save_model to ensure passwords are
    always stored as secure hashes in myAiPA.
    Never stores plain text passwords — ever.
    """
    def save_model(self, request, obj, form, change):

        # If password has been changed or user is new
        if obj.pk is None or form.cleaned_data.get('password1'):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
