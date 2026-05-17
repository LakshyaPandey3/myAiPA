# accounts/views.py
# This file contains all authentication views for myAiPA.
# Each view handles one specific API endpoint.
# Views receive requests, use serializers to validate data,
# perform business logic, and return JSON responses.

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
)


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for a user.
    Called after successful registration and login.
    Returns both tokens as a dictionary so views
    can include them in their responses.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


"""
Handles new user registration for myAiPA.
Accepts POST requests with user details.
Validates data through RegisterSerializer.
Creates user and returns JWT tokens on success.
No authentication required — this is a public endpoint.
"""
class RegisterView(APIView):
    # AllowAny means anyone can access this endpoint.
    # No JWT token required — user does not have one yet.
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST /api/auth/register/
        Creates a new myAiPA user account.
        Returns user profile and JWT tokens on success.
        Returns validation errors on failure.
        """
        # Pass request data to serializer for validation.
        # If any field is invalid — serializer catches it
        # and we never reach the user creation code.
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            # All data is valid — create the user.
            # serializer.save() calls our create() method
            # which calls create_user() with hashed password.
            user = serializer.save()

            # Generate JWT tokens for the new user
            # so they are logged in immediately after
            # registration — no need to login separately.
            tokens = get_tokens_for_user(user)

            return Response({
                'success': True,
                'message': (
                    f'Welcome to myAiPA! '
                    f'Your personal assistant '
                    f'{user.myAiPA_name} is ready '
                    f'to meet you.'
                ),
                'data': {
                    'user': UserProfileSerializer(user).data,
                    'tokens': tokens,
                }
            }, status=status.HTTP_201_CREATED)

        # Serializer found validation errors.
        # Return them clearly so React can display
        # the right error message to the user.
        return Response({
            'success': False,
            'message': 'Registration failed.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)