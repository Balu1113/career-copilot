from pathlib import Path

from django.conf import settings
from django.http import FileResponse

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from resumes.models import Resume

from .models import GeneratedResume, ResumeProfile, ResumeTemplate
from .serializers import (
    GeneratedResumeSerializer,
    ResumeTemplateSerializer,
)
from .services.docx_renderer import render_resume_to_docx
from .services.pdf_renderer import render_resume_to_pdf
from .services.resume_generator import (
    generate_resume_optimization,
    generate_resume_summary,
    modify_resume_content,
)
from .services.resume_parser import (
    parse_resume_text,
)


def _render_generated_resume_docx(
    generated_resume,
    content,
):
    """
    Render a GeneratedResume's content to a DOCX file and
    store the resulting output file path on the instance.

    The caller is responsible for saving the instance.
    """

    output_dir = (
        Path(settings.MEDIA_ROOT)
        / "generated_resumes"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    is_uploaded_modifier = bool(
        generated_resume.source_resume
        and generated_resume.mode
        == GeneratedResume.MODE_MODIFIER
    )

    output_extension = (
        "pdf" if is_uploaded_modifier else "docx"
    )

    output_filename = (
        f"resume_{generated_resume.id}."
        f"{output_extension}"
    )

    output_path = output_dir / output_filename

    template_data = {}

    if generated_resume.template:
        template_data = (
            generated_resume
            .template
            .template_data
            or {}
        )

    if is_uploaded_modifier:
        render_resume_to_pdf(
            content=content,
            template_data={
                **template_data,
                "uploaded_layout": True,
            },
            output_path=output_path,
        )
    else:
        render_resume_to_docx(
            content=content,
            template_data=template_data,
            output_path=output_path,
        )

    generated_resume.output_file = (
        f"generated_resumes/{output_filename}"
    )


class ResumeTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        templates = (
            ResumeTemplate.objects
            .filter(user=request.user)
            .order_by("-created_at")
        )

        serializer = ResumeTemplateSerializer(
            templates,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = ResumeTemplateSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True
        )

        template = serializer.save()

        return Response(
            ResumeTemplateSerializer(
                template
            ).data,
            status=status.HTTP_201_CREATED,
        )

class ResumeTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, template_id):
        try:
            template = ResumeTemplate.objects.get(
                id=template_id,
                user=request.user,
            )
        except ResumeTemplate.DoesNotExist:
            return Response(
                {"detail": "Template not found."},
                status=404,
            )

        template.delete()

        return Response(
            {"detail": "Template deleted successfully."},
            status=204,
        )


class ResumeProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = ResumeProfile.objects.get_or_create(user=request.user)
        return Response(
            {
                "personal": profile.personal,
                "experience": profile.experience,
                "education": profile.education,
                "certifications": profile.certifications,
                "publications": profile.publications,
            }
        )

    def patch(self, request):
        profile, _ = ResumeProfile.objects.get_or_create(user=request.user)

        allowed_fields = [
            "personal",
            "experience",
            "education",
            "certifications",
            "publications",
        ]

        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])

        profile.save(update_fields=allowed_fields + ["updated_at"])

        return Response(
            {
                "personal": profile.personal,
                "experience": profile.experience,
                "education": profile.education,
                "certifications": profile.certifications,
                "publications": profile.publications,
            }
        )


class GeneratedResumeListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        generated_resumes = (
            GeneratedResume.objects
            .filter(user=request.user)
            .select_related(
                "template",
                "source_resume",
            )
            .order_by("-created_at")
        )

        serializer = GeneratedResumeSerializer(
            generated_resumes,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = GeneratedResumeSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        generated_resume = serializer.save(
            user=request.user
        )

        return Response(
            GeneratedResumeSerializer(
                generated_resume
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ResumeContentGenerationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source_type = request.data.get(
            "source_type",
            "existing_resume",
        )

        resume_id = request.data.get(
            "resume_id"
        )

        template_id = request.data.get(
            "template_id"
        )

        job_description = (
            request.data.get(
                "job_description",
                "",
            )
            .strip()
        )

        # -------------------------------------------------
        # Basic validation
        # -------------------------------------------------

        if source_type not in {
            "existing_resume",
            "new_resume",
        }:
            return Response(
                {
                    "detail": (
                        "source_type must be "
                        "'existing_resume' or "
                        "'new_resume'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not template_id:
            return Response(
                {
                    "detail": (
                        "template_id is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not job_description:
            return Response(
                {
                    "detail": (
                        "job_description is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # Validate template ownership
        # -------------------------------------------------

        try:
            template = ResumeTemplate.objects.get(
                id=template_id,
                user=request.user,
            )
        except ResumeTemplate.DoesNotExist:
            return Response(
                {
                    "detail": "Template not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        resume = None

        try:
            # =================================================
            # EXISTING RESUME FLOW
            # =================================================

            if source_type == "existing_resume":

                if not resume_id:
                    return Response(
                        {
                            "detail": (
                                "resume_id is required "
                                "for existing_resume."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    resume = Resume.objects.get(
                        id=resume_id,
                        user=request.user,
                    )
                except Resume.DoesNotExist:
                    return Response(
                        {
                            "detail": "Resume not found."
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if not resume.extracted_text:
                    return Response(
                        {
                            "detail": (
                                "Selected resume does "
                                "not contain extracted text."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # ---------------------------------------------
                # Parse existing resume
                # ---------------------------------------------

                parsed_resume = parse_resume_text(
                    resume.extracted_text
                )

                if hasattr(
                    parsed_resume,
                    "model_dump",
                ):
                    parsed_resume = (
                        parsed_resume.model_dump()
                    )

                # ---------------------------------------------
                # Optimize ONLY skills and projects
                # ---------------------------------------------

                optimization = (
                    generate_resume_optimization(
                        skills=parsed_resume.get(
                            "skills",
                            {},
                        ),
                        projects=parsed_resume.get(
                            "projects",
                            [],
                        ),
                        job_description=job_description,
                    )
                )

                if hasattr(
                    optimization,
                    "model_dump",
                ):
                    optimization = (
                        optimization.model_dump()
                    )

                # ---------------------------------------------
                # Preserve all other resume sections
                # ---------------------------------------------

                final_content = {
                    "personal": parsed_resume.get(
                        "personal",
                        {},
                    ),
                    "summary": parsed_resume.get(
                        "summary",
                        "",
                    ),
                    "skills": optimization.get(
                        "skills",
                        {},
                    ),
                    "experience": parsed_resume.get(
                        "experience",
                        [],
                    ),
                    "projects": optimization.get(
                        "projects",
                        [],
                    ),
                    "education": parsed_resume.get(
                        "education",
                        [],
                    ),
                    "certifications": parsed_resume.get(
                        "certifications",
                        [],
                    ),
                    "publications": parsed_resume.get(
                        "publications",
                        [],
                    ),
                }

            # =================================================
            # NEW RESUME FLOW
            # =================================================

            else:

                # ---------------------------------------------
                # Get user's resume profile for prefill
                # ---------------------------------------------

                profile, _ = ResumeProfile.objects.get_or_create(user=request.user)

                # ---------------------------------------------
                # No existing resume.
                #
                # Generate only JD-driven skills/projects.
                # Prefill other sections from user profile.
                # ---------------------------------------------

                optimization = (
                    generate_resume_optimization(
                        skills={},
                        projects=[],
                        job_description=job_description,
                    )
                )

                if hasattr(
                    optimization,
                    "model_dump",
                ):
                    optimization = (
                        optimization.model_dump()
                    )

                final_content = {
                    "personal": profile.personal or {},
                    "summary": "",
                    "skills": optimization.get(
                        "skills",
                        {},
                    ),
                    "experience": profile.experience or [],
                    "projects": optimization.get(
                        "projects",
                        [],
                    ),
                    "education": profile.education or [],
                    "certifications": profile.certifications or [],
                    "publications": profile.publications or [],
                }

            # =================================================
            # CREATE GENERATED RESUME
            # =================================================

            generated_resume = (
                GeneratedResume.objects.create(
                    user=request.user,
                    template=template,
                    source_resume=resume,
                    title=(
                        "Generated Resume"
                        if resume is None
                        else (
                            f"Generated Resume - "
                            f"{resume.title}"
                        )
                    ),
                    mode=GeneratedResume.MODE_BUILDER,
                    job_description=job_description,
                    content=final_content,
                    status=(
                        GeneratedResume.STATUS_GENERATING
                    ),
                )
            )

            # =================================================
            # RENDER DOCX
            # =================================================

            output_dir = (
                Path(settings.MEDIA_ROOT)
                / "generated_resumes"
            )

            output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_filename = (
                f"resume_{generated_resume.id}.docx"
            )

            output_path = (
                output_dir / output_filename
            )

            template_data = (
                template.template_data or {}
            )

            render_resume_to_docx(
                content=final_content,
                template_data=template_data,
                output_path=output_path,
            )

            # =================================================
            # SAVE GENERATED FILE
            # =================================================

            generated_resume.output_file = (
                f"generated_resumes/"
                f"{output_filename}"
            )

            generated_resume.status = (
                GeneratedResume.STATUS_COMPLETED
            )

            generated_resume.error_message = ""

            generated_resume.save(
                update_fields=[
                    "output_file",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            # =================================================
            # RESPONSE
            # =================================================

            return Response(
                {
                    "id": generated_resume.id,
                    "source_type": source_type,
                    "resume_id": (
                        resume.id
                        if resume
                        else None
                    ),
                    "template_id": template.id,
                    "content": final_content,
                    "output_file": (
                        generated_resume
                        .output_file
                        .url
                        if generated_resume.output_file
                        else None
                    ),
                    "status": (
                        generated_resume.status
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            # ---------------------------------------------
            # If the GeneratedResume record was created,
            # mark it as failed.
            # ---------------------------------------------

            if "generated_resume" in locals():

                generated_resume.status = (
                    GeneratedResume.STATUS_FAILED
                )

                generated_resume.error_message = (
                    str(exc)
                )

                generated_resume.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "updated_at",
                    ]
                )

            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )


class ResumeSummaryGenerationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        content = request.data.get("content")
        job_description = (
            request.data.get("job_description", "")
            or ""
        )

        if content is None:
            return Response(
                {
                    "detail": "Resume content is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            summary = generate_resume_summary(
                content,
                job_description=job_description,
            )

            return Response(
                {"summary": summary},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {
                    "detail": (
                        f"Failed to generate professional summary: {str(exc)}"
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GeneratedResumeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, resume_id):
        try:
            generated_resume = (
                GeneratedResume.objects.get(
                    id=resume_id,
                    user=request.user,
                )
            )
        except GeneratedResume.DoesNotExist:
            return Response(
                {
                    "detail": "Generated resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        content = request.data.get("content")

        if not isinstance(content, dict):
            return Response(
                {
                    "detail": (
                        "content must be a JSON object."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_sections = [
            "personal",
            "summary",
            "skills",
            "experience",
            "projects",
            "education",
            "certifications",
            "publications",
        ]

        missing_sections = [
            section
            for section in required_sections
            if section not in content
        ]

        if missing_sections:
            return Response(
                {
                    "detail": (
                        "Missing sections: "
                        + ", ".join(missing_sections)
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # ---------------------------------------------
            # Save edited content
            # ---------------------------------------------

            generated_resume.content = content
            generated_resume.status = (
                GeneratedResume.STATUS_GENERATING
            )
            generated_resume.error_message = ""

            generated_resume.save(
                update_fields=[
                    "content",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            # Render the updated file using the source-aware renderer.
            _render_generated_resume_docx(
                generated_resume,
                content,
            )

            generated_resume.status = (
                GeneratedResume.STATUS_COMPLETED
            )

            generated_resume.error_message = ""

            generated_resume.save(
                update_fields=[
                    "content",
                    "output_file",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            # Save profile data (excluding skills)
            # ---------------------------------------------

            profile, _ = ResumeProfile.objects.get_or_create(user=request.user)

            profile_fields = [
                "personal",
                "experience",
                "education",
                "certifications",
                "publications",
            ]

            for field in profile_fields:
                if field in content:
                    setattr(profile, field, content[field])

            profile.save(update_fields=profile_fields + ["updated_at"])

            # ---------------------------------------------
            # RETURN RESPONSE
            # ---------------------------------------------

            return Response(
                {
                    "id": generated_resume.id,
                    "content": generated_resume.content,
                    "output_file": (
                        generated_resume
                        .output_file
                        .url
                    ),
                    "status": (
                        generated_resume.status
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            generated_resume.status = (
                GeneratedResume.STATUS_FAILED
            )

            generated_resume.error_message = str(
                exc
            )

            generated_resume.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )

    def delete(self, request, resume_id):
        try:
            generated_resume = (
                GeneratedResume.objects.get(
                    id=resume_id,
                    user=request.user,
                )
            )
        except GeneratedResume.DoesNotExist:
            return Response(
                {
                    "detail": "Generated resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        generated_resume.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class GeneratedResumeAIEditView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        try:
            generated_resume = (
                GeneratedResume.objects.get(
                    id=resume_id,
                    user=request.user,
                )
            )
        except GeneratedResume.DoesNotExist:
            return Response(
                {
                    "detail": "Generated resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        instruction = (
            request.data.get("instruction", "")
            or ""
        ).strip()

        if not instruction:
            return Response(
                {
                    "detail": (
                        "instruction is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        job_description = (
            request.data.get(
                "job_description",
                "",
            )
            or ""
        )

        try:
            updated_content = (
                modify_resume_content(
                    generated_resume.content
                    or {},
                    instruction,
                    job_description=(
                        job_description
                    ),
                )
            )

            generated_resume.content = (
                updated_content
            )

            generated_resume.status = (
                GeneratedResume.STATUS_GENERATING
            )

            generated_resume.error_message = ""

            _render_generated_resume_docx(
                generated_resume,
                updated_content,
            )

            generated_resume.status = (
                GeneratedResume.STATUS_COMPLETED
            )

            generated_resume.save(
                update_fields=[
                    "content",
                    "output_file",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "id": generated_resume.id,
                    "content": generated_resume.content,
                    "output_file": (
                        generated_resume
                        .output_file
                        .url
                        if generated_resume.output_file
                        else None
                    ),
                    "status": (
                        generated_resume.status
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            generated_resume.status = (
                GeneratedResume.STATUS_FAILED
            )

            generated_resume.error_message = str(
                exc
            )

            generated_resume.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )


class UploadedResumeEditForkView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _source_file_url(request, resume):
        if not resume.file:
            return None

        return request.build_absolute_uri(
            resume.file.url
        )

    def post(self, request, resume_id):
        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {
                    "detail": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        existing_fork = (
            GeneratedResume.objects
            .filter(
                user=request.user,
                source_resume=resume,
                mode=GeneratedResume.MODE_MODIFIER,
            )
            .order_by("-created_at")
            .first()
        )

        if existing_fork:
            return Response(
                {
                    "id": existing_fork.id,
                    "title": existing_fork.title,
                    "mode": existing_fork.mode,
                    "source_file": self._source_file_url(
                        request,
                        resume,
                    ),
                    "content": existing_fork.content,
                    "output_file": (
                        existing_fork
                        .output_file
                        .url
                        if existing_fork.output_file
                        else None
                    ),
                    "status": existing_fork.status,
                    "created_at": (
                        existing_fork.created_at
                    ),
                },
                status=status.HTTP_200_OK,
            )

        if not resume.extracted_text.strip():
            return Response(
                {
                    "detail": (
                        "Resume text has not been "
                        "extracted yet."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content = parse_resume_text(
                resume.extracted_text
            )

            generated_resume = (
                GeneratedResume.objects.create(
                    user=request.user,
                    source_resume=resume,
                    title=(
                        resume.title
                    ),
                    mode=(
                        GeneratedResume.MODE_MODIFIER
                    ),
                    content=content,
                    status=(
                        GeneratedResume
                        .STATUS_GENERATING
                    ),
                )
            )

            _render_generated_resume_docx(
                generated_resume,
                content,
            )

            generated_resume.status = (
                GeneratedResume.STATUS_COMPLETED
            )

            generated_resume.save(
                update_fields=[
                    "output_file",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "id": generated_resume.id,
                    "title": generated_resume.title,
                    "mode": generated_resume.mode,
                    "source_file": self._source_file_url(
                        request,
                        resume,
                    ),
                    "content": generated_resume.content,
                    "output_file": (
                        generated_resume
                        .output_file
                        .url
                        if generated_resume.output_file
                        else None
                    ),
                    "status": (
                        generated_resume.status
                    ),
                    "created_at": (
                        generated_resume.created_at
                    ),
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )


class GeneratedResumeDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        resume_id,
    ):
        try:
            generated_resume = (
                GeneratedResume.objects.get(
                    id=resume_id,
                    user=request.user,
                )
            )

        except GeneratedResume.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Generated resume not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            generated_resume.mode
            == GeneratedResume.MODE_MODIFIER
            and generated_resume.source_resume
        ):
            _render_generated_resume_docx(
                generated_resume,
                generated_resume.content or {},
            )
            generated_resume.save(
                update_fields=[
                    "output_file",
                    "updated_at",
                ]
            )

        if not generated_resume.output_file:
            return Response(
                {
                    "detail": (
                        "Generated resume file "
                        "is not available."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            file_handle = (
                generated_resume.output_file.open(
                    "rb"
                )
            )

            suffix = (
                ".pdf"
                if generated_resume.output_file.name.lower().endswith(".pdf")
                else ".docx"
            )

            filename = (
                f"{generated_resume.title}{suffix}"
            )

            return FileResponse(
                file_handle,
                as_attachment=True,
                filename=filename,
            )

        except FileNotFoundError:
            return Response(
                {
                    "detail": (
                        "Generated resume file "
                        "was not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )