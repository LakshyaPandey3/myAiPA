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
        'email',
        'username',
        'myAiPA_name',
        'timezone',
        'briefing_time',
        'streak_count',
        'is_active',
        'is_staff',
        'last_login',
        'created_at',
    )

    # Filter buttons on the right side of admin panel.
    # Lets us segment users by important categories
    # instantly without writing any database queries.
    list_filter = (
        'is_staff',
        'is_active',
        'timezone',
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

    # NOTE: save_model is NOT overridden here.
    # Django's UserAdmin handles password hashing
    # correctly through UserCreationForm automatically.
    # A custom save_model that calls set_password()
    # would double-hash the password and break login.