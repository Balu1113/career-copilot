from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from django.urls import reverse

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from resumes.models import Resume, ResumeIntelligence

from .models import GeneratedResume, ResumeProfile, ResumeTemplate
from .serializers import (
    GeneratedResumeSerializer,
    ResumeTemplateSerializer,
)
from .services.builtin_templates import ensure_builtin_templates
from .services.docx_renderer import render_resume_to_docx
from .services.pdf_renderer import render_resume_to_pdf
from .services.resume_generator import (
    generate_resume_optimization,
    generate_resume_projects,
    generate_resume_summary,
    modify_resume_content,
)
from .services.template_analyzer import analyze_template
from .services.resume_naming import build_generated_resume_title
from .services.resume_parser import (
    complete_resume_content,
    parse_resume_text,
)
from .schemas import ordered_resume_sections


def _generated_resume_template_data(generated_resume):
    snapshot = generated_resume.template_data_snapshot
    if isinstance(snapshot, dict) and snapshot:
        return dict(snapshot)
    if generated_resume.template:
        return generated_resume.template.template_data or {}
    return {}


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

    # Reproduce the layout resolved when this resume was generated instead
    # of re-analyzing the source file on every render.
    template_data = _generated_resume_template_data(generated_resume)

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


def _generated_resume_download_url(generated_resume):
    if not generated_resume.output_file:
        return None

    return reverse(
        "generated-resume-download",
        kwargs={"resume_id": generated_resume.id},
    ).removeprefix("/api/")


def _resume_education_fallback(resume):
    try:
        return resume.intelligence.education
    except ResumeIntelligence.DoesNotExist:
        return []


def _matching_source_projects(source_projects, selected_projects):
    selected_names = {
        str(project.get("name", "")).strip().casefold()
        for project in selected_projects
        if isinstance(project, dict) and project.get("name")
    }
    return [
        project
        for project in source_projects
        if isinstance(project, dict)
        and str(project.get("name", "")).strip().casefold() in selected_names
    ]


class ResumeTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_builtin_templates(request.user)

        templates = (
            ResumeTemplate.objects
            .filter(user=request.user)
            .order_by("-is_builtin", "-created_at")
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

        if template.is_builtin:
            return Response(
                {"detail": "Built-in templates cannot be deleted."},
                status=400,
            )

        template.delete()

        return Response(
            {"detail": "Template deleted successfully."},
            status=204,
        )


class ResumeTemplateSampleDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, template_id):
        try:
            template = ResumeTemplate.objects.get(
                id=template_id,
                user=request.user,
            )
        except ResumeTemplate.DoesNotExist:
            return Response({"detail": "Template not found."}, status=404)

        if not template.sample_file:
            return Response(
                {"detail": "Template sample is not available."},
                status=404,
            )

        try:
            file_handle = template.sample_file.open("rb")
        except FileNotFoundError:
            return Response(
                {"detail": "Template sample file was not found."},
                status=404,
            )

        return FileResponse(
            file_handle,
            filename=Path(template.sample_file.name).name,
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
            .filter(
                user=request.user,
                mode=GeneratedResume.MODE_BUILDER,
            )
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
            data=request.data,
            context={"request": request},
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

        resume_type = request.data.get(
            "resume_type",
            "uploaded",
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


        use_source_layout = bool(request.data.get("use_source_layout"))

        job_title = str(
            request.data.get("job_title") or ""
        ).strip()

        company = str(
            request.data.get("company") or ""
        ).strip()

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

        template = None
        if template_id:
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
        generated_source = None

        try:
            # =================================================
            # EXISTING RESUME FLOW
            # =================================================

            if source_type == "existing_resume":

                if resume_type not in {
                    "uploaded",
                    "generated",
                }:
                    return Response(
                        {
                            "detail": (
                                "resume_type must be "
                                "'uploaded' or 'generated'."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

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

                if resume_type == "uploaded":

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
                    # Fill parser omissions (name, contact details,
                    # education) from the source text or the saved
                    # intelligence profile before building content.
                    # ---------------------------------------------

                    parsed_resume = complete_resume_content(
                        parsed_resume,
                        resume.extracted_text,
                        _resume_education_fallback(resume),
                    )

                else:

                    try:
                        generated_source = (
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
                        generated_source.status
                        != GeneratedResume.STATUS_COMPLETED
                        or not isinstance(
                            generated_source.content,
                            dict,
                        )
                        or not generated_source.content
                    ):
                        return Response(
                            {
                                "detail": (
                                    "Selected generated resume "
                                    "does not contain completed resume "
                                    "content."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    parsed_resume = (
                        generated_source.content
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
                        allow_new_projects=False,
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
                    "projects": _matching_source_projects(
                        parsed_resume.get("projects", []),
                        optimization.get("projects", []),
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

            if template:
                template_data = template.template_data or {}
            elif resume:
                template_data = analyze_template(resume.file.path)
            elif (
                generated_source
                and generated_source.template_id
            ):
                template = generated_source.template
                template_data = template.template_data or {}
            elif (
                generated_source
                and generated_source.source_resume
            ):
                template_data = analyze_template(
                    generated_source.source_resume.file.path
                )
            else:
                ensure_builtin_templates(request.user)
                template = (
                    ResumeTemplate.objects
                    .filter(
                        user=request.user,
                        is_builtin=True,
                    )
                    .order_by("id")
                    .first()
                )
                if not template:
                    raise ValueError(
                        "No resume template is available."
                    )
                template_data = template.template_data or {}

            final_content["section_order"] = ordered_resume_sections(
                final_content,
                template_data,
            )

            source_title = None

            if resume:
                source_title = resume.title
            elif generated_source:
                source_title = generated_source.title

            generated_resume = (
                GeneratedResume.objects.create(
                    user=request.user,
                    template=template,
                    source_resume=resume,
                    title=build_generated_resume_title(
                        job_description=job_description,
                        job_title=job_title,
                        company=company,
                        source_title=source_title,
                    ),
                    mode=GeneratedResume.MODE_BUILDER,
                    job_description=job_description,
                    content=final_content,
                    status=(
                        GeneratedResume.STATUS_GENERATING
                    ),
                    template_data_snapshot=template_data,
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
                    "resume_type": (
                        resume_type
                        if source_type == "existing_resume"
                        else None
                    ),
                    "resume_id": (
                        resume.id
                        if resume
                        else (
                            generated_source.id
                            if generated_source
                            else None
                        )
                    ),
                    "title": generated_resume.title,
                    "template_id": (
                        template.id if template else None
                    ),
                    "template_data": template_data,
                    "content": final_content,
                    "output_file": _generated_resume_download_url(
                        generated_resume
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


class ResumeProjectsGenerationView(APIView):
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
            projects = generate_resume_projects(
                content,
                job_description=job_description,
            )

            return Response(
                {"projects": projects},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {
                    "detail": (
                        "Failed to generate projects: "
                        f"{str(exc)}"
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
                    "output_file": _generated_resume_download_url(
                        generated_resume
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
                    "output_file": _generated_resume_download_url(
                        generated_resume
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

        download_format = request.query_params.get("export_format")
        if download_format is not None:
            download_format = download_format.lower()
            if download_format not in {"pdf", "word"}:
                return Response(
                    {"detail": "format must be either 'pdf' or 'word'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            output_dir = Path(settings.MEDIA_ROOT) / "generated_resumes"
            output_dir.mkdir(parents=True, exist_ok=True)
            suffix = ".pdf" if download_format == "pdf" else ".docx"
            output_path = output_dir / (
                f"resume_{generated_resume.id}_download{suffix}"
            )
            template_data = _generated_resume_template_data(generated_resume)
            content = generated_resume.content or {}

            if download_format == "pdf":
                render_resume_to_pdf(
                    content=content,
                    template_data={
                        **template_data,
                        "uploaded_layout": bool(
                            generated_resume.mode
                            == GeneratedResume.MODE_MODIFIER
                            and generated_resume.source_resume
                        ),
                        "fit_to_page": True,
                    },
                    output_path=output_path,
                )
            else:
                render_resume_to_docx(
                    content=content,
                    template_data={
                        **template_data,
                        "one_page_export": True,
                    },
                    output_path=output_path,
                )

            return FileResponse(
                output_path.open("rb"),
                as_attachment=True,
                filename=f"{generated_resume.title}{suffix}",
            )

        if (
            not generated_resume.output_file
            or (
                generated_resume.mode
                == GeneratedResume.MODE_MODIFIER
                and generated_resume.source_resume
            )
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
                {"detail": "Generated resume file could not be generated."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            _render_generated_resume_docx(
                generated_resume,
                generated_resume.content or {},
            )
            generated_resume.save(
                update_fields=["output_file", "updated_at"]
            )
            try:
                file_handle = generated_resume.output_file.open("rb")
            except FileNotFoundError:
                return Response(
                    {"detail": "Generated resume file could not be regenerated."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            suffix = (
                ".pdf"
                if generated_resume.output_file.name.lower().endswith(".pdf")
                else ".docx"
            )
            return FileResponse(
                file_handle,
                as_attachment=True,
                filename=f"{generated_resume.title}{suffix}",
            )