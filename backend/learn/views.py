from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LearnSession
from .serializers import (
    LearnMessageSerializer,
    LearnSessionCreateSerializer,
)
from .services.tutorial_tutor import generate_tutor_reply


def serialize_session(session, include_messages=False):
    data = {
        "id": session.id,
        "title": session.title,
        "level": session.level,
        "message_count": len(session.messages or []),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }

    if include_messages:
        data["messages"] = session.messages or []

    return data


class LearnSessionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = LearnSession.objects.filter(
            user=request.user
        )

        return Response(
            [
                serialize_session(session)
                for session in sessions
            ],
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = LearnSessionCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        session = LearnSession.objects.create(
            user=request.user,
            level=serializer.validated_data.get(
                "level",
                "beginner",
            ),
            title="",
            messages=[],
        )

        return Response(
            serialize_session(
                session,
                include_messages=True,
            ),
            status=status.HTTP_201_CREATED,
        )


class LearnSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_session(self, request, session_id):
        try:
            return LearnSession.objects.get(
                pk=session_id,
                user=request.user,
            )
        except LearnSession.DoesNotExist:
            return None

    def get(self, request, session_id):
        session = self._get_session(
            request,
            session_id,
        )

        if session is None:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            serialize_session(
                session,
                include_messages=True,
            ),
            status=status.HTTP_200_OK,
        )

    def delete(self, request, session_id):
        session = self._get_session(
            request,
            session_id,
        )

        if session is None:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        session.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class LearnSessionMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = LearnSession.objects.get(
                pk=session_id,
                user=request.user,
            )
        except LearnSession.DoesNotExist:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LearnMessageSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data[
            "content"
        ].strip()

        history = session.messages or []

        try:
            reply = generate_tutor_reply(
                message=message,
                history=history,
                level=session.level,
            )
        except Exception as exc:
            return Response(
                {
                    "detail": (
                        "Failed to generate a lesson: "
                        f"{str(exc)}"
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        user_message = {
            "role": "user",
            "content": message,
        }

        assistant_message = {
            "role": "assistant",
            "content": reply,
        }

        session.messages = [
            *history,
            user_message,
            assistant_message,
        ]

        if not session.title:
            session.title = message[:60]

        session.save()

        return Response(
            {
                "session": serialize_session(session),
                "reply": reply,
            },
            status=status.HTTP_200_OK,
        )
