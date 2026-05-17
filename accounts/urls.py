# accounts/urls.py
# This file defines all authentication URL endpoints
# for myAiPA. Every URL here is prefixed with /api/auth/
# because of how we included it in core/urls.py.

from django.urls import path
from .views import RegisterView

urlpatterns = [
    # POST /api/auth/register/
    # Creates a new myAiPA user account.
    # Public endpoint — no authentication required.
    path('register/', RegisterView.as_view(), name='register'),
]