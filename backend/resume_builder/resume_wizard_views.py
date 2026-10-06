import logging
from uuid import uuid4

from django.db import IntegrityError, transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GeneratedResume
from .resume_wizard_serializers import (
    ResumeWizardFinalizeRequestSerializer,
    ResumeWizardFinalizeResponseSerializer,
    ResumeWizardTurnRequestSerializer,
    ResumeWizardTurnResponseSerializer,
)
from .services.resume_wizard import (
    RESUME_WIZARD_MAX_QUESTIONS,
    apply_back,
    apply_review,
    build_initial_wizard_state,
    normalize_resume_data,
    run_ai_turn,
    wizard_data_to_generated_content,
)
from .views import _render_generated_resume_docx

logger = logging.getLogger(__name__)


def _finalize_payload(resume):
    return {
        "message": "Master resume created.",
        "request_id": str(uuid4()),
        "resume_id": resume.id,
        "processing_status": "ready",
        "is_master": resume.is_master,
    }


def _same_master(resume, *, content, title):
    return (
        resume.is_master
        and resume.status == GeneratedResume.STATUS_COMPLETED
        and resume.title == title
        and (resume.content or {}).get("wizard_data") == content
    )


def _master_conflict():
    return Response(
        {"detail": "A master resume already exists. Delete it before creating a new one."},
        status=status.HTTP_409_CONFLICT,
    )


class ResumeWizardTurnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResumeWizardTurnRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        action = values["action"]

        if action == "start":
            state = build_initial_wizard_state()
        else:
            state = values.get("state")
            if not isinstance(state, dict):
                raise serializers.ValidationError(
                    {"state": "A wizard state object is required."}
                )
            if not isinstance(state.get("asked_count", 0), int) or isinstance(
                state.get("asked_count", 0), bool
            ) or state.get("asked_count", 0) < 0:
                raise serializers.ValidationError(
                    {"state": {"asked_count": "Must be a non-negative integer."}}
                )
            if not isinstance(state.get("resume_data"), dict):
                raise serializers.ValidationError(
                    {"state": {"resume_data": "Must be a JSON object."}}
                )
            if action == "back":
                state = apply_back(state)
            elif action == "review":
                state = apply_review(state)
            elif int(state.get("asked_count", 0)) >= RESUME_WIZARD_MAX_QUESTIONS:
                state = apply_review(state)
            else:
                answer = values.get("answer") or {}
                if action == "answer" and not answer.get("text", "").strip():
                    raise serializers.ValidationError(
                        {"answer": {"text": "A non-empty answer is required."}}
                    )
                try:
                    state = run_ai_turn(
                        state,
                        answer.get("text", ""),
                        skip=action == "skip",
                        output_language=values.get("output_language", "en"),
                    )
                except ValueError:
                    logger.exception("Resume wizard turn returned invalid data")
                    return Response(
                        {"detail": "Could not update the resume draft."},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )
                except Exception:
                    logger.exception("Resume wizard turn failed")
                    return Response(
                        {"detail": "Resume wizard failed. Please try again."},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )

        response_serializer = ResumeWizardTurnResponseSerializer(data={"state": state})
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data)


class ResumeWizardFinalizeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_serializer = ResumeWizardFinalizeRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        state = request_serializer.validated_data["state"]
        if not isinstance(state, dict) or not isinstance(state.get("resume_data"), dict):
            raise serializers.ValidationError(
                {"state": "A valid wizard state with resume_data is required."}
            )

        try:
            data = normalize_resume_data(state["resume_data"])
        except ValueError as error:
            raise serializers.ValidationError(
                {"state": {"resume_data": str(error)}}
            ) from error

        if state.get("current_section") != "review" or not state.get("is_complete"):
            raise serializers.ValidationError(
                {"state": "Complete the resume and review it before finalizing."}
            )

        content = wizard_data_to_generated_content(data)
        title_name = (data.get("personalInfo", {}).get("name") or "Resume").strip()
        title = f"{title_name[:130]} Master Resume"

        try:
            with transaction.atomic():
                existing = GeneratedResume.objects.filter(
                    user=request.user,
                    is_master=True,
                ).first()
                if existing:
                    if _same_master(existing, content= data, title=title):
                        response_serializer = ResumeWizardFinalizeResponseSerializer(
                            data=_finalize_payload(existing)
                        )
                        response_serializer.is_valid(raise_exception=True)
                        return Response(response_serializer.data)
                    return _master_conflict()

                resume = GeneratedResume.objects.create(
                    user=request.user,
                    title=title,
                    mode=GeneratedResume.MODE_BUILDER,
                    status=GeneratedResume.STATUS_GENERATING,
                    content=content,
                    is_master=True,
                )
                _render_generated_resume_docx(resume, content)
                resume.status = GeneratedResume.STATUS_COMPLETED
                resume.error_message = ""
                resume.save(
                    update_fields=["output_file", "status", "error_message", "updated_at"]
                )
        except IntegrityError:
            existing = GeneratedResume.objects.filter(
                user=request.user,
                is_master=True,
            ).first()
            if existing and _same_master(existing, content=data, title=title):
                return Response(_finalize_payload(existing))
            return _master_conflict()
        except Exception:
            logger.exception("Resume wizard finalize failed for user %s", request.user.pk)
            return Response(
                {"detail": "Could not create master resume."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = ResumeWizardFinalizeResponseSerializer(
            data=_finalize_payload(resume)
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)