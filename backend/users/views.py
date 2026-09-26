from datetime import timedelta

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


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

        now = timezone.now()

        access_token = AccessToken.for_user(user)
        access_token.set_exp(lifetime=timedelta(minutes=30))
        access_token_expires_at = now + timedelta(minutes=30)

        return Response(
            {
                "access": str(access_token),
                "access_token_expires_at": access_token_expires_at,
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

        return Response(
            {
                "message":
                "Password changed successfully."
            }
        )