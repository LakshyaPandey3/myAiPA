# accounts/urls.py
# This file defines all authentication URL endpoints
# for myAiPA. Every URL here is prefixed with /api/auth/
# because of how we included it in core/urls.py.

from django.urls import path
from .views import RegisterView, LoginView, LogoutView

urlpatterns = [
    # POST /api/auth/register/
    # Creates a new myAiPA user account.
    # Public endpoint — no authentication required.
    path('register/', RegisterView.as_view(), name='register'),

    # POST /api/auth/login/
    # Authenticates existing myAiPA user.
    # Accepts email OR username as identifier.
    # Public endpoint — no authentication required.
    path('login/', LoginView.as_view(), name='login'),

    # POST /api/auth/logout/
    # Blacklists refresh token permanently.
    # Protected endpoint — must be logged in.
    path('logout/', LogoutView.as_view(), name='logout'),

]