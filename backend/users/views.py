import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
)


def _token_pair_for_user(user):
    now = timezone.now()
    access_token = AccessToken.for_user(user)
    access_token.set_exp(lifetime=timedelta(minutes=30))
    refresh_token = RefreshToken.for_user(user)
    refresh_token.set_exp(lifetime=timedelta(days=30))

    return {
        "access": str(access_token),
        "refresh": str(refresh_token),
        "access_token_expires_at": now + timedelta(minutes=30),
        "refresh_token_expires_at": now + timedelta(days=30),
        "user": UserSerializer(user).data,
    }


def _blacklist_user_refresh_tokens(user):
    for outstanding_token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding_token)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_token_pair_for_user(user), status=201)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        now = timezone.now()

        access_token = AccessToken.for_user(user)
        access_token.set_exp(lifetime=timedelta(minutes=30))
        access_token_expires_at = now + timedelta(minutes=30)

        # Refresh token: long-lived. While valid, the user stays signed in.
        refresh_token = RefreshToken.for_user(user)
        refresh_token.set_exp(lifetime=timedelta(days=30))
        refresh_token_expires_at = now + timedelta(days=30)

        return Response(
            {
                "access": str(access_token),
                "refresh": str(refresh_token),
                "access_token_expires_at": access_token_expires_at,
                "refresh_token_expires_at": refresh_token_expires_at,
                "user": UserSerializer(user).data,
            }
        )


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            user = User.objects.get(pk=refresh["user_id"])
        except (TokenError, User.DoesNotExist, KeyError):
            return Response(
                {
                    "error":
                    "Invalid or expired refresh token."
                },
                status=400,
            )

        if not user.is_active:
            return Response(
                {"error": "This account has been disabled."},
                status=400,
            )

        access_token = AccessToken.for_user(user)
        access_token.set_exp(lifetime=timedelta(minutes=30))
        refresh.blacklist()
        new_refresh = RefreshToken.for_user(user)
        new_refresh.set_exp(lifetime=timedelta(days=30))
        now = timezone.now()

        return Response(
            {
                "access": str(access_token),
                "refresh": str(new_refresh),
                "access_token_expires_at": now + timedelta(minutes=30),
                "refresh_token_expires_at": now + timedelta(days=30),
            }
        )


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=400,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=400,
            )

        return Response(
            {"message": "Logged out successfully."},
            status=200,
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            UserSerializer(request.user).data
        )


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(
            serializer.validated_data["old_password"]
        ):
            return Response(
                {
                    "error":
                    "Current password is incorrect."
                },
                status=400,
            )

        user.set_password(
            serializer.validated_data["new_password"]
        )

        user.save()
        _blacklist_user_refresh_tokens(user)

        return Response(
            {
                "message":
                "Password changed successfully."
            }
        )


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip()
        user = User.objects.filter(email__iexact=email, is_active=True).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            frontend_url = os.getenv(
                "FRONTEND_URL",
                "http://localhost:5173",
            ).rstrip("/")
            reset_url = f"{frontend_url}/reset-password/{uid}/{token}"
            send_mail(
                "Reset your Career Copilot password",
                f"Use this link to reset your password: {reset_url}",
                None,
                [user.email],
                fail_silently=False,
            )

        return Response(
            {
                "message": (
                    "If an account with that email exists, "
                    "a password reset link has been sent."
                )
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, UnicodeDecodeError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "This password reset link is invalid or expired."},
                status=400,
            )

        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        _blacklist_user_refresh_tokens(user)

        return Response({"message": "Password reset successfully."})