# accounts/urls.py
# This file defines all authentication URL endpoints
# for myAiPA. Every URL here is prefixed with /api/auth/
# because of how we included it in core/urls.py.

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    UpdateProfileView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Public endpoints — no token required
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Token refresh — handled by simplejwt automatically
    # Accepts refresh token — returns new access token
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Protected endpoints — valid JWT token required
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('me/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]