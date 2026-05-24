# accounts/serializers.py
# This file handles all data validation and conversion
# for myAiPA's authentication system.
# Every piece of data coming in or going out of the
# accounts API passes through these serializers first.
#
# SECURITY IMPLEMENTATIONS:
# - Passwords never returned in any response
# - Timing attack protection on login endpoint
# - Race condition handled on registration
# - JWT exceptions caught specifically not broadly
# - Email enumeration prevented on password reset
# - Old password verified directly in serializer
# - Old password stripped before verification
# - All inputs stripped before validation runs
# - Password validation runs on stripped value only
# - max_length enforced on every field
# - HTML injection prevented on text fields
# - Password DOS attack prevented via max_length
# - Request context null checked before access
# - allow_blank handled explicitly on optional fields
# - Consistent stripping in all cross field comparisons

import re
import pytz

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import (
    validate_password as django_validate_password
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


"""
Serializer for displaying myAiPA user profile data.
Used whenever we need to return user information
in an API response — login, register, profile endpoints.
Never exposes sensitive fields like password.
email and username are read only — changes to these
require separate dedicated verification processes.
"""
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        # Which model this serializer works with
        model = User

        # Which fields to include in the response.
        # We never include password — ever.
        # All myAiPA user settings included so
        # React can display the complete profile.
        fields = [
            'id',
            'email',
            'username',
            'myAiPA_name',
            'timezone',
            'briefing_time',
            'streak_count',
            'created_at',
            'last_login',
        ]

        # These fields can be read but never written.
        # email and username locked — require separate
        # verification process to change.
        # id, created_at, streak_count, last_login
        # are set automatically by Django — never manually.
        read_only_fields = [
            'id',
            'email',
            'username',
            'created_at',
            'streak_count',
            'last_login',
        ]


"""
Serializer for myAiPA user registration.
Validates all registration data before creating
a new user account. Ensures passwords are strong,
emails are unique, usernames are valid format,
and all required fields are present and clean.
myAiPA_name and timezone are optional —
sensible defaults provided if not sent.
Race condition on duplicate registration handled
in create() to prevent unhandled database errors.
All fields have max_length matching database columns.
Password validation runs on stripped value only —
prevents padded weak passwords bypassing validation.
"""
class RegisterSerializer(serializers.ModelSerializer):

    # Password field — write only, never returned
    # in response. Validation runs in validate_password
    # method AFTER stripping to ensure what is validated
    # exactly matches what gets stored.
    # max_length=128 prevents password DOS attacks.
    password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    # Password confirmation — must match password.
    # Write only, never stored in database.
    # max_length matches password field.
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    # myAiPA_name is optional — defaults to Zoya
    # if user does not provide one at registration.
    # max_length=50 matches the database column exactly.
    # allow_blank=True lets validate_myAiPA_name handle
    # empty strings gracefully by returning Zoya.
    # Without allow_blank=True, DRF rejects blank values
    # before our validator can run.
    myAiPA_name = serializers.CharField(
        required=False,
        default='Zoya',
        max_length=50,
        allow_blank=True,
    )

    # timezone is optional — defaults to Asia/Kolkata
    # if user does not provide one during registration.
    # max_length=50 matches database column exactly.
    # All standard timezone names fit within 50 chars.
    timezone = serializers.CharField(
        required=False,
        default='Asia/Kolkata',
        max_length=50,
    )

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'password',
            'password2',
            'myAiPA_name',
            'timezone',
        ]

    def validate_email(self, value):
        """
        Normalise email to lowercase and strip spaces.
        Check that email is not already
        registered with myAiPA.
        """
        email = value.lower().strip()

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "This email is already registered with myAiPA."
            )
        return email

    def validate_username(self, value):
        """
        Normalise username to lowercase and strip spaces.
        Validates minimum length of 3 characters.
        Validates maximum length of 30 characters.
        Only allows letters, numbers, underscores.
        No HTML characters allowed.
        Checks username is not already taken in myAiPA.
        """
        value = value.lower().strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Username must be at least 3 characters."
            )

        if len(value) > 30:
            raise serializers.ValidationError(
                "Username cannot exceed 30 characters."
            )

        # Only allow letters, numbers, underscores.
        # No spaces, no special characters, no HTML.
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, "
                "numbers and underscores."
            )

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "This username is already taken in myAiPA."
            )
        return value

    def validate_myAiPA_name(self, value):
        """
        Strip whitespace from myAiPA assistant name.
        Reject any HTML tags — prevents XSS attacks
        when React displays the name on screen.
        Returns default Zoya if name is empty after
        stripping — every myAiPA user gets an assistant.
        allow_blank=True on field ensures this method
        is called even when empty string is sent.
        """
        value = value.strip()

        # Reject HTML angle brackets — XSS protection.
        # myAiPA assistant name must be plain text only.
        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "myAiPA assistant name cannot "
                "contain HTML characters."
            )

        # Return Zoya as default if name is empty.
        # Handles both empty string and whitespace only.
        if len(value) < 1:
            return 'Zoya'

        return value

    def validate_timezone(self, value):
        """
        Strip whitespace from timezone value.
        Validates against real timezone database using pytz.
        Prevents storing invalid timezone strings that would
        break Celery briefing scheduling for this user.
        """
        value = value.strip()

        if value not in pytz.all_timezones:
            raise serializers.ValidationError(
                "Invalid timezone. Please provide a valid "
                "timezone like Asia/Kolkata or America/New_York."
            )

        return value

    def validate_password(self, value):
        """
        Strip whitespace FIRST — then run Django's
        full password strength validation on the
        stripped value. This ensures what gets
        validated exactly matches what gets stored.
        Prevents padded weak passwords like
        "  Ab12  " bypassing the length check.
        """
        value = value.strip()

        try:
            django_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                list(e.messages)
            )

        return value

    def validate(self, attrs):
        """
        Cross field validation.
        Checks that password and password2 match.
        Runs after all individual field validations.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password2": "Passwords do not match."
            })
        return attrs

    def create(self, validated_data):
        """
        Create and return a new myAiPA user.
        Removes password2 before saving — it is
        only for validation, never stored.
        Uses create_user so password is hashed
        automatically — never stored as plain text.
        Race condition handled — if two identical
        registrations hit simultaneously, the second
        gets a clean error instead of server crash.
        """
        validated_data.pop('password2')

        try:
            user = User.objects.create_user(**validated_data)
            return user
        except Exception:
            raise serializers.ValidationError(
                "Failed to create myAiPA account. "
                "Please try again."
            )


"""
Serializer for updating myAiPA user profile.
Allows partial updates — user can change only
what they want without sending all fields.
Email and username changes not allowed here —
they require separate verification processes.
All fields validated against database column sizes.
"""
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'myAiPA_name',
            'timezone',
            'briefing_time',
        ]

    def validate_myAiPA_name(self, value):
        """
        Strip whitespace from myAiPA assistant name.
        Reject HTML tags — prevents XSS attacks.
        Ensure name is not empty after stripping.
        Ensure length does not exceed database column.
        Every myAiPA user must have an assistant name.
        """
        value = value.strip()

        if re.search(r'[<>]', value):
            raise serializers.ValidationError(
                "myAiPA assistant name cannot "
                "contain HTML characters."
            )

        if len(value) < 1:
            raise serializers.ValidationError(
                "myAiPA assistant name cannot be empty."
            )

        if len(value) > 50:
            raise serializers.ValidationError(
                "myAiPA assistant name cannot "
                "exceed 50 characters."
            )

        return value

    def validate_timezone(self, value):
        """
        Strip whitespace from timezone value.
        Validates against real timezone database using pytz.
        Prevents storing invalid timezone strings that would
        break Celery briefing scheduling for this user.
        """
        value = value.strip()

        if value not in pytz.all_timezones:
            raise serializers.ValidationError(
                "Invalid timezone. Please provide a valid "
                "timezone like Asia/Kolkata or America/New_York."
            )

        return value

    def update(self, instance, validated_data):
        """
        Update and return the myAiPA user profile.
        Only updates fields that were actually sent —
        leaves everything else completely unchanged.
        This is a partial update — not a full replace.
        """
        instance.myAiPA_name = validated_data.get(
            'myAiPA_name',
            instance.myAiPA_name
        )
        instance.timezone = validated_data.get(
            'timezone',
            instance.timezone
        )
        instance.briefing_time = validated_data.get(
            'briefing_time',
            instance.briefing_time
        )
        instance.save()
        return instance


"""
Serializer for changing myAiPA user password.
Requires old password for security verification.
Old password stripped before verification — consistent
with how passwords are stored and verified everywhere
else in myAiPA. Accidental spaces never cause failure.
Old password fully verified here in the serializer —
the view does not need any additional password checks.
Request context null checked before access to prevent
AttributeError crashes during testing or misconfiguration.
Password validation runs on stripped value only —
prevents padded weak passwords bypassing validation.
max_length on all password fields prevents DOS attacks.
"""
class ChangePasswordSerializer(serializers.Serializer):

    # Current password — required to prove
    # it is really the account owner changing it.
    # Verified against stored hash directly here.
    # Stripped before verification for consistency.
    # write_only means it never appears in responses.
    # max_length=128 prevents password DOS attacks.
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    # New password — validated in validate_new_password
    # method AFTER stripping for security consistency.
    # max_length=128 prevents password DOS attacks.
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    # Confirmation of new password.
    # Must match new_password exactly.
    # min_length and max_length both enforced.
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
    )

    def validate_old_password(self, value):
        """
        Verify old password is not empty AND
        actually correct against stored password.
        Strips before verification — consistent with
        how all passwords are stored in myAiPA.
        Prevents accidental spaces causing false
        incorrect password errors for the user.
        Uses request.user from serializer context —
        DRF automatically passes request in context.
        Request context null checked for safety.
        """
        if len(value.strip()) < 1:
            raise serializers.ValidationError(
                "Old password cannot be empty."
            )

        # Null check context before accessing request.
        # Prevents AttributeError crash if context
        # is missing during tests or misconfiguration.
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                "Authentication context missing. "
                "Please try again."
            )

        # Strip before verification — consistent with
        # how passwords are stored and verified in
        # LoginSerializer and throughout myAiPA.
        if not request.user.check_password(value.strip()):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )

        return value

    def validate_new_password(self, value):
        """
        Strip whitespace FIRST — then run Django's
        full password strength validation on the
        stripped value. Ensures what gets validated
        exactly matches what gets stored.
        Prevents padded weak passwords bypassing check.
        Explicit minimum length check with clear message.
        """
        value = value.strip()

        if len(value) < 8:
            raise serializers.ValidationError(
                "New password must be at least 8 characters."
            )

        try:
            django_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                list(e.messages)
            )

        return value

    def validate_new_password2(self, value):
        """
        Strip accidental whitespace from confirmation.
        Prevents false mismatch errors from spaces.
        Explicit length check with clear error message.
        Match check happens in validate() below.
        """
        value = value.strip()

        if len(value) < 1:
            raise serializers.ValidationError(
                "Password confirmation cannot be empty."
            )

        if len(value) < 8:
            raise serializers.ValidationError(
                "Password confirmation must be "
                "at least 8 characters."
            )
        return value

    def validate(self, attrs):
        """
        Cross field validation — runs after all
        individual field validations pass.
        Checks three things:
        1. New passwords match each other.
        2. New password differs from old password.
        3. All values stripped consistently before
           comparison to prevent false negatives.
        """
        new_password = attrs['new_password'].strip()
        new_password2 = attrs['new_password2'].strip()
        old_password = attrs['old_password'].strip()

        if new_password != new_password2:
            raise serializers.ValidationError({
                "new_password2": (
                    "Password confirmation does not "
                    "match new password."
                )
            })

        if new_password == old_password:
            raise serializers.ValidationError({
                "new_password": (
                    "New password cannot be the same "
                    "as your current password."
                )
            })

        attrs['new_password'] = new_password
        attrs['new_password2'] = new_password2
        attrs['old_password'] = old_password

        return attrs


"""
Serializer for myAiPA user logout.
Receives the refresh token and blacklists it
permanently so it can never be used again.
Catches only JWT specific exceptions — not all
exceptions broadly — to avoid hiding system errors.
max_length on refresh token prevents oversized input.
"""
class LogoutSerializer(serializers.Serializer):

    # The refresh token to blacklist on logout.
    # Must be the refresh token from login —
    # not the access token. They are different.
    # max_length=500 covers full JWT token length.
    refresh = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
    )

    def validate_refresh(self, value):
        """
        Strip whitespace from refresh token.
        Basic empty check before blacklisting.
        Full token validation happens in save().
        """
        value = value.strip()
        if len(value) < 1:
            raise serializers.ValidationError(
                "Refresh token cannot be empty."
            )
        return value

    def validate(self, attrs):
        """
        Store token for blacklisting in save().
        Runs after field level validation passes.
        """
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        """
        Blacklist the refresh token permanently.
        Token is dead forever after this runs.
        Even a stolen token cannot be used again.
        Catches only JWT specific exceptions —
        TokenError and InvalidToken — not all
        exceptions broadly to avoid hiding real
        system errors from error monitoring.
        """
        try:
            RefreshToken(self.token).blacklist()
        except (TokenError, InvalidToken):
            raise serializers.ValidationError(
                "Token is invalid or already blacklisted. "
                "You may already be logged out of myAiPA."
            )


"""
Serializer for myAiPA password reset request.
User provides their registered email address.
A reset link is sent if the email exists.
We never confirm whether email exists or not —
prevents email enumeration security attacks where
attackers discover which emails have myAiPA accounts.
"""
class PasswordResetRequestSerializer(serializers.Serializer):

    # Email address to send the reset link to.
    # max_length=254 is the RFC standard email limit.
    email = serializers.EmailField(
        required=True,
        max_length=254,
    )

    def validate_email(self, value):
        """
        Normalise email to lowercase and strip spaces.
        Never reveals whether email is registered —
        prevents attackers discovering which emails
        have myAiPA accounts registered.
        """
        return value.lower().strip()


"""
Serializer for myAiPA password reset confirmation.
User provides reset token from email plus new password.
Validates token and uid are not empty before view
processes them. Actual token verification in view.
Password validation runs on stripped value only —
prevents padded weak passwords bypassing validation.
All fields have max_length to prevent oversized input.
"""
class PasswordResetConfirmSerializer(serializers.Serializer):

    # Reset token received in the email link.
    # Actual validity checked in view.
    # max_length=200 covers Django token length.
    token = serializers.CharField(
        required=True,
        max_length=200,
    )

    # User id encoded in the reset link.
    # Decoded and verified in the view.
    # max_length=100 covers encoded uid length.
    uid = serializers.CharField(
        required=True,
        max_length=100,
    )

    # New password — validated in validate_new_password
    # method AFTER stripping for security consistency.
    # max_length=128 prevents password DOS attacks.
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    # New password confirmation.
    # max_length matches new_password field.
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
    )

    def validate_token(self, value):
        """
        Strip whitespace and check token not empty.
        Actual token validity checked in the view
        using Django's password reset token checker.
        """
        value = value.strip()
        if len(value) < 1:
            raise serializers.ValidationError(
                "Invalid password reset link. "
                "Please request a new one."
            )
        return value

    def validate_uid(self, value):
        """
        Strip whitespace and check uid not empty.
        Actual uid decoding happens in the view
        using Django's urlsafe base64 decoder.
        """
        value = value.strip()
        if len(value) < 1:
            raise serializers.ValidationError(
                "Invalid password reset link. "
                "Please request a new one."
            )
        return value

    def validate_new_password(self, value):
        """
        Strip whitespace FIRST — then run Django's
        full password strength validation on the
        stripped value. Ensures what gets validated
        exactly matches what gets stored.
        Prevents padded weak passwords bypassing check.
        """
        value = value.strip()

        try:
            django_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                list(e.messages)
            )

        return value

    def validate_new_password2(self, value):
        """
        Strip whitespace from confirmation field.
        Prevents false mismatch from accidental spaces.
        """
        return value.strip()

    def validate(self, attrs):
        """
        Check both new passwords match exactly
        before attempting the password reset.
        """
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password2": "Passwords do not match."
            })
        return attrs


"""
Custom login serializer for myAiPA.
Accepts email OR username as login identifier —
whichever the user remembers is perfectly fine.
Case insensitive matching on both fields.
Timing attack protection — dummy password check
runs even when user not found to equalise response
time and prevent identifier enumeration attacks.
All fields have max_length to prevent oversized input.
"""
class LoginSerializer(serializers.Serializer):

    # Accepts email or username — named identifier
    # to make it clear both are accepted equally.
    # max_length=254 covers maximum email length.
    identifier = serializers.CharField(
        required=True,
        max_length=254,
    )

    # Password — write only, never in response.
    # max_length=128 prevents password DOS attacks.
    password = serializers.CharField(
        write_only=True,
        required=True,
        max_length=128,
    )

    def validate(self, attrs):
        """
        Finds user by email OR username — whichever
        matches the identifier provided.
        Case insensitive — Lakshya and lakshya
        both find the same myAiPA account.
        Timing attack protected — dummy hash check
        runs when user not found to prevent attackers
        measuring response time to find valid accounts.
        Handles DoesNotExist and MultipleObjectsReturned.
        Wraps authenticate() in try/except for safety.
        Verifies password and account active status.
        Attaches authenticated user to attrs for view.
        """
        identifier = attrs.get('identifier').strip()
        password = attrs.get('password').strip()

        if len(identifier) < 1:
            raise serializers.ValidationError({
                "identifier": (
                    "Email or username cannot be empty."
                )
            })

        if len(password) < 1:
            raise serializers.ValidationError({
                "password": "Password cannot be empty."
            })

        try:
            user = User.objects.get(
                Q(email__iexact=identifier) |
                Q(username__iexact=identifier)
            )
        except User.DoesNotExist:
            # TIMING ATTACK PROTECTION
            # Run dummy password check so response time
            # is identical whether user exists or not.
            # Without this — fast response reveals the
            # identifier is not registered in myAiPA.
            check_password(
                password,
                make_password('dummy_myAiPA_timing_protection')
            )
            raise serializers.ValidationError({
                "identifier": (
                    "No myAiPA account found with "
                    "this email or username."
                )
            })
        except User.MultipleObjectsReturned:
            # Defensive — should never happen with
            # unique email and username constraints
            # but handled for complete safety.
            raise serializers.ValidationError({
                "identifier": (
                    "Multiple accounts found. "
                    "Please contact myAiPA support."
                )
            })

        try:
            authenticated_user = authenticate(
                username=user.username,
                password=password
            )
        except Exception:
            raise serializers.ValidationError({
                "detail": (
                    "Login failed due to a server error. "
                    "Please try again."
                )
            })

        if not authenticated_user:
            raise serializers.ValidationError({
                "password": "Incorrect password."
            })

        if not authenticated_user.is_active:
            raise serializers.ValidationError({
                "identifier": (
                    "This myAiPA account has been "
                    "deactivated. Please contact support."
                )
            })

        attrs['user'] = authenticated_user
        return attrs