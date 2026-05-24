# core/urls.py
# This is the main URL router for myAiPA.
# Every request that comes into the backend
# passes through here first and gets routed
# to the correct app's urls.py file.

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # All authentication endpoints live under /api/auth/
    path('api/auth/', include('accounts.urls')),

    # Task management endpoints
    path('api/tasks/', include('tasks.urls')),
]