from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import FileResponse
import threading
from users.models import UserProfile

from .models import Resume, ResumeIntelligence
from .serializers import ResumeSerializer, ResumeIntelligenceSerializer
from .services.resume_processing import process_resume_ai
from .services.resume_intelligence import generate_resume_intelligence

class ResumeListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = ResumeSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        return Resume.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        resume = serializer.save(user=self.request.user)

        print(
            f"[RESUME UPLOAD] Resume {resume.id} saved. "
            f"Starting AI processing thread.",
            flush=True,
        )

        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user
        )

        if profile.active_resume_id is None:
            profile.active_resume = resume
            profile.save(update_fields=["active_resume"])

        threading.Thread(
            target=process_resume_ai,
            args=(resume.id,),
            daemon=True,
        ).start()

        print(
            f"[RESUME UPLOAD] AI processing thread started "
            f"for resume {resume.id}.",
            flush=True,
        )


class ResumeDetailView(
    generics.RetrieveDestroyAPIView
):
    serializer_class = ResumeSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):
        return Resume.objects.filter(
            user=self.request.user
        )


class SetActiveResumeView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, pk):

        try:
            resume = Resume.objects.get(
                id=pk,
                user=request.user,
            )

        except Resume.DoesNotExist:
            return Response(
                {
                    "error": "Resume not found."
                },
                status=404,
            )

        profile, _ = UserProfile.objects.get_or_create(
            user=request.user
        )

        profile.active_resume = resume

        profile.save(
            update_fields=["active_resume"]
        )

        return Response({
            "message": "Active resume updated.",
            "active_resume_id": resume.id,
        })


class ResumeDownloadView(APIView):
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(
                id=pk,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {"error": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not resume.file:
            return Response(
                {
                    "error": "Resume file is not available."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            filename = (
                resume.file.name
                .rsplit("/", 1)[-1]
            )

            file_handle = resume.file.open("rb")

            return FileResponse(
                file_handle,
                as_attachment=True,
                filename=filename,
            )
        except FileNotFoundError:
            return Response(
                {
                    "error": "Resume file was not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class ResumeIntelligenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(
                id=pk,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {"error": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            intelligence = resume.intelligence
        except ResumeIntelligence.DoesNotExist:
            return Response(
                {
                    "error": "Resume intelligence has not been generated yet."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResumeIntelligenceSerializer(
            intelligence
        )

        return Response(serializer.data)


class GenerateResumeIntelligenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(
                id=pk,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {"error": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not resume.extracted_text.strip():
            return Response(
                {"error": "Resume text has not been extracted yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            intelligence = generate_resume_intelligence(
                resume.extracted_text
            )

            ResumeIntelligence.objects.update_or_create(
                resume=resume,
                defaults=intelligence.model_dump(),
            )

            return Response(
                ResumeIntelligenceSerializer(
                    ResumeIntelligence.objects.get(resume=resume)
                ).data,
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            return Response(
                {
                    "error": f"Failed to generate resume intelligence: {str(exc)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )