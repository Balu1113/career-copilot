import logging
from pathlib import Path

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import FileResponse
from users.models import UserProfile

from resume_builder.services.pdf_renderer import render_resume_to_pdf
from resume_builder.services.resume_generator import modify_resume_content
from resume_builder.services.resume_parser import (
    complete_resume_content,
    parse_resume_text,
)

from .models import Resume, ResumeIntelligence
from .serializers import ResumeSerializer, ResumeIntelligenceSerializer
from .services.resume_intelligence import generate_resume_intelligence
from .services.resume_jobs import (
    reset_and_schedule,
    schedule_resume_processing,
    schedule_stuck_resumes,
)

logger = logging.getLogger(__name__)

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

    def list(self, request, *args, **kwargs):
        queryset = list(self.filter_queryset(self.get_queryset()))

        # Self-heal: kick AI processing for resumes stuck in
        # pending/processing (e.g. queued before the worker ran).
        spawned = schedule_stuck_resumes(queryset)

        if spawned:
            for resume in queryset:
                if resume.processing_status in (
                    "pending",
                    "processing",
                ):
                    resume.refresh_from_db()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        resume = serializer.save(user=self.request.user)
        schedule_resume_processing(resume)

        profile, _ = UserProfile.objects.get_or_create(
            user=self.request.user
        )

        if profile.active_resume_id is None:
            profile.active_resume = resume
            profile.save(update_fields=["active_resume"])



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


class ResumeProcessView(APIView):
    """Restart AI processing for a failed or stuck resume."""

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
                {"error": "Resume not found."},
                status=404,
            )

        reset_and_schedule(resume)
        resume.refresh_from_db()

        return Response(
            ResumeSerializer(resume).data,
            status=202,
        )


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


class ResumeContentView(APIView):
    """Read and write the editable content of an uploaded resume.

    The edits live on the uploaded Resume itself, so editing never
    creates an extra resume in the generated resumes list.
    """

    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _resume(request, pk):
        try:
            return Resume.objects.get(
                id=pk,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return None

    @staticmethod
    def _as_dict(content):
        if hasattr(content, "model_dump"):
            return content.model_dump()
        return content

    @staticmethod
    def _payload(resume, content=None):
        return {
            "id": resume.id,
            "title": resume.title,
            "source_file": (
                Path(resume.file.name).name
                if resume.file
                else ""
            ),
            "content": (
                content
                if content is not None
                else resume.builder_content
            ),
        }

    @staticmethod
    def _education_fallback(resume):
        try:
            return resume.intelligence.education
        except ResumeIntelligence.DoesNotExist:
            return []

    @staticmethod
    def _missing(request):
        return Response(
            {"detail": "Resume not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def get(self, request, pk):
        resume = self._resume(request, pk)
        if resume is None:
            return self._missing(request)

        if resume.builder_content:
            return Response(self._payload(resume))

        if not resume.extracted_text.strip():
            return Response(
                {
                    "detail": (
                        "Resume text has not been extracted yet."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content = complete_resume_content(
                self._as_dict(
                    parse_resume_text(resume.extracted_text)
                ),
                resume.extracted_text,
                self._education_fallback(resume),
            )
        except Exception as exc:
            logger.exception(
                "Resume content extraction failed for %s",
                resume.pk,
            )
            return Response(
                {"detail": f"Could not read this resume: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        resume.builder_content = content
        resume.save(
            update_fields=["builder_content", "updated_at"]
        )

        return Response(self._payload(resume, content))

    def patch(self, request, pk):
        resume = self._resume(request, pk)
        if resume is None:
            return self._missing(request)

        content = request.data.get("content")

        if not isinstance(content, dict):
            return Response(
                {"detail": "content must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume.builder_content = content
        resume.save(
            update_fields=["builder_content", "updated_at"]
        )

        return Response(self._payload(resume, content))


class ResumeContentAIEditView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(
                id=pk,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        instruction = str(
            request.data.get("instruction") or ""
        ).strip()

        if not instruction:
            return Response(
                {"detail": "An instruction is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not resume.builder_content:
            return Response(
                {"detail": "Load the resume before editing it."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content = modify_resume_content(
                resume.builder_content,
                instruction,
                str(request.data.get("job_description") or ""),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception(
                "AI edit failed for resume %s",
                resume.pk,
            )
            return Response(
                {"detail": f"AI edit failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        content = ResumeContentView._as_dict(content)

        resume.builder_content = content
        resume.save(
            update_fields=["builder_content", "updated_at"]
        )

        return Response(
            {
                "id": resume.id,
                "content": content,
            }
        )


class ResumeEditedDownloadView(APIView):
    """Download the edited version of an uploaded resume."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(
                id=pk,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {"detail": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not resume.builder_content:
            return Response(
                {"detail": "This resume has no edited version."},
                status=status.HTTP_404_NOT_FOUND,
            )

        output_dir = (
            Path(settings.MEDIA_ROOT) / "edited_resumes"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"resume_{resume.id}.pdf"

        try:
            render_resume_to_pdf(
                content=resume.builder_content,
                output_path=output_path,
                template_data={"uploaded_layout": True},
            )
        except Exception as exc:
            logger.exception(
                "Could not render edited resume %s",
                resume.pk,
            )
            return Response(
                {"detail": f"Could not render the resume: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return FileResponse(
            open(output_path, "rb"),
            as_attachment=True,
            filename=f"{resume.title or 'resume'}.pdf",
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
                defaults=intelligence if isinstance(intelligence, dict)
                else intelligence.model_dump(),
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