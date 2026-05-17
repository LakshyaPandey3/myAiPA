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




"""
Handles user login for myAiPA.
Accepts POST requests with identifier and password.
Identifier can be email OR username — either works.
Returns JWT tokens on successful login.
No authentication required — public endpoint.
"""
class LoginView(APIView):
    # Public endpoint — user has no token yet
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST /api/auth/login/
        Authenticates existing myAiPA user.
        Returns user profile and JWT tokens on success.
        Returns error on invalid credentials.
        """
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            # serializer.validated_data['user'] is set
            # inside LoginSerializer.validate() after
            # successful authentication. We access it here.
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)

            return Response({
                'success': True,
                'message': (
                    f'Welcome back! '
                    f'{user.myAiPA_name} missed you.'
                ),
                'data': {
                    'user': UserProfileSerializer(user).data,
                    'tokens': tokens,
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Login failed.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


"""
Handles user logout for myAiPA.
Accepts POST requests with refresh token.
Blacklists the token permanently on logout.
Authentication required — must be logged in to logout.
"""
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle POST /api/auth/logout/
        Blacklists the refresh token permanently.
        Token cannot be used again after this.
        """
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': (
                    'You have been logged out of myAiPA. '
                    'See you tomorrow!'
                ),
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Logout failed.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)




"""
Returns the current logged in myAiPA user's profile.
Called by React whenever it needs current user data.
Authentication required — must be logged in.
"""
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET /api/auth/me/
        Returns complete profile of logged in user.
        request.user is automatically set by Django
        from the JWT token in the request header.
        """
        serializer = UserProfileSerializer(request.user)

        return Response({
            'success': True,
            'data': {
                'user': serializer.data,
            }
        }, status=status.HTTP_200_OK)




"""
Handles myAiPA user profile updates.
Accepts PATCH requests with fields to update.
Only updates fields that are actually sent —
leaves everything else completely unchanged.
Authentication required — must be logged in.
"""
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        """
        Handle PATCH /api/auth/me/update/
        Partial update — only sent fields are updated.
        User can change myAiPA_name, timezone,
        briefing_time without affecting other fields.
        """
        serializer = UpdateProfileSerializer(
            # instance is the current user — we are
            # updating this object not creating new one
            instance=request.user,
            # data is what React sent to update
            data=request.data,
            # partial=True means not all fields required
            # user can send just one field if they want
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                'success': True,
                'message': (
                    'Your myAiPA profile has been updated.'
                ),
                'data': {
                    'user': UserProfileSerializer(
                        request.user
                    ).data,
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Profile update failed.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


"""
Handles password change for logged in myAiPA user.
Requires old password for security verification.
Old password is verified in the serializer itself —
this view just needs to set the new password.
Authentication required — must be logged in.
"""
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle POST /api/auth/change-password/
        Verifies old password and sets new password.
        Serializer handles old password verification.
        View just calls set_password and saves.
        """
        # Pass context with request so serializer
        # can access request.user for old password
        # verification inside validate_old_password.
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Old password already verified in serializer.
            # Just set the new password and save.
            request.user.set_password(
                serializer.validated_data['new_password']
            )
            request.user.save()

            return Response({
                'success': True,
                'message': (
                    'Your password has been changed. '
                    'Please login again with your new password.'
                ),
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Password change failed.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

"""
Handles password reset request for myAiPA.
User provides their email address.
If email exists — sends password reset link.
We never reveal whether email exists or not —
prevents email enumeration attacks.
No authentication required — user is logged out.
"""
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST /api/auth/password-reset/
        Sends password reset email if account exists.
        Always returns success — even if email not found.
        This prevents revealing which emails are registered.
        """
        serializer = PasswordResetRequestSerializer(
            data=request.data
        )

        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Check if user exists with this email.
            # We use filter() not get() to avoid exception.
            try:
                user = User.objects.get(email=email)

                # Generate password reset token
                from django.contrib.auth.tokens import (
                    default_token_generator
                )
                from django.utils.http import (
                    urlsafe_base64_encode
                )
                from django.utils.encoding import (
                    force_bytes
                )

                # uid encodes the user's id safely
                uid = urlsafe_base64_encode(
                    force_bytes(user.pk)
                )
                # token is a secure one-time use string
                token = default_token_generator.make_token(
                    user
                )

                # TODO: Send actual email in production.
                # For now we return the reset link directly
                # so we can test without email setup.
                reset_link = (
                    f'http://localhost:5173/reset-password'
                    f'?uid={uid}&token={token}'
                )

                # In production replace above with:
                # send_mail(subject, message, from, [email])

            except User.DoesNotExist:
                # User not found — but we still return
                # success to prevent email enumeration.
                pass

        # Always return success regardless of whether
        # email exists — security best practice.
        return Response({
            'success': True,
            'message': (
                'If this email is registered with myAiPA, '
                'you will receive a password reset link shortly.'
            ),
        }, status=status.HTTP_200_OK)


"""
Handles password reset confirmation for myAiPA.
User provides uid, token from email link
plus their new password.
Verifies token is valid before resetting.
No authentication required — user is logged out.
"""
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST /api/auth/password-reset/confirm/
        Verifies reset token and sets new password.
        Token is single use — cannot be reused.
        """
        serializer = PasswordResetConfirmSerializer(
            data=request.data
        )

        if serializer.is_valid():
            from django.contrib.auth.tokens import (
                default_token_generator
            )
            from django.utils.http import (
                urlsafe_base64_decode
            )
            from django.utils.encoding import (
                force_str
            )

            try:
                # Decode the uid to get the user's pk
                uid = force_str(
                    urlsafe_base64_decode(
                        serializer.validated_data['uid']
                    )
                )
                user = User.objects.get(pk=uid)

            except (User.DoesNotExist, ValueError, TypeError):
                return Response({
                    'success': False,
                    'message': 'Invalid password reset link.',
                    'errors': {
                        'uid': ['Invalid or expired reset link.']
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify the token is valid and not expired
            token = serializer.validated_data['token']
            if not default_token_generator.check_token(
                user, token
            ):
                return Response({
                    'success': False,
                    'message': 'Invalid or expired reset link.',
                    'errors': {
                        'token': [
                            'Reset link has expired. '
                            'Please request a new one.'
                        ]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Token is valid — set the new password
            user.set_password(
                serializer.validated_data['new_password']
            )
            user.save()

            return Response({
                'success': True,
                'message': (
                    'Your password has been reset. '
                    'You can now login with your new password.'
                ),
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Password reset failed.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


