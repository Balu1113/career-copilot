import json
import logging
import re

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .enrichment_schemas import (
    EnhancedBulletsOutput,
    RegeneratedBulletsOutput,
    RegeneratedSkillsOutput,
    ResumeEnrichmentAnalysisOutput,
)
from .enrichment_serializers import (
    AnalysisResultSerializer,
    ApplyEnhancementsRequestSerializer,
    ApplyRegeneratedRequestSerializer,
    EnhanceRequestSerializer,
    EnhancementPreviewSerializer,
    RegenerateRequestSerializer,
    RegenerateResponseSerializer,
)
from .models import GeneratedResume
from .services.resume_enrichment_prompts import (
    ANALYZE_RESUME_PROMPT,
    ENHANCE_DESCRIPTION_PROMPT,
    REGENERATE_ITEM_PROMPT,
    REGENERATE_SKILLS_PROMPT,
)
from .services.resume_processing_prompts import get_language_name
from agents.services.structured_llm import generate_structured_output
from .views import _generated_resume_download_url, _render_generated_resume_docx

logger = logging.getLogger(__name__)


def _description_list(value):
    if isinstance(value, list):
        return [str(line) for line in value if str(line).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _resume_details(content):
    details = {}
    content = content if isinstance(content, dict) else {}
    for index, item in enumerate(content.get("experience", [])):
        if not isinstance(item, dict):
            continue
        item_id = f"exp_{index}"
        details[item_id] = {
            "item_id": item_id,
            "item_type": "experience",
            "title": item.get("role", ""),
            "subtitle": item.get("company", ""),
            "current_description": _description_list(item.get("bullets")),
        }
    for index, item in enumerate(content.get("projects", [])):
        if not isinstance(item, dict):
            continue
        item_id = f"proj_{index}"
        description = _description_list(item.get("description"))
        description.extend(_description_list(item.get("bullets")))
        details[item_id] = {
            "item_id": item_id,
            "item_type": "project",
            "title": item.get("name", ""),
            "subtitle": item.get("role", ""),
            "current_description": description,
        }
    return details


def _validate_llm_result(schema, result):
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    return schema.model_validate(result).model_dump()


def _get_resume(request, resume_id):
    try:
        return GeneratedResume.objects.get(id=resume_id, user=request.user), None
    except GeneratedResume.DoesNotExist:
        return None, Response(
            {"detail": "Generated resume not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


def _save_enriched_content(resume, content):
    resume.content = content
    try:
        _render_generated_resume_docx(resume, content)
    except Exception:
        logger.exception("Failed to render enriched resume %s", resume.id)
        return Response(
            {"detail": "Resume changes could not be rendered."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    resume.status = GeneratedResume.STATUS_COMPLETED
    resume.error_message = ""
    resume.save(
        update_fields=["content", "output_file", "status", "error_message", "updated_at"]
    )
    return Response(
        {
            "message": "Resume updated successfully.",
            "content": resume.content,
            "output_file": _generated_resume_download_url(resume),
        }
    )


def _analysis_prompt(content, output_language):
    return ANALYZE_RESUME_PROMPT.format(
        resume_json=json.dumps(content, ensure_ascii=False),
        output_language=output_language,
    )


class ResumeEnrichmentAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        resume, error = _get_resume(request, resume_id)
        if error:
            return error
        if not isinstance(resume.content, dict) or not resume.content:
            return Response(
                {"detail": "Resume has no processed content."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output_language = get_language_name(
            request.data.get("output_language", "en")
        )
        try:
            result = generate_structured_output(
                system_prompt=(
                    "You are a truthful resume analyst. Return only the requested JSON."
                ),
                user_prompt=_analysis_prompt(resume.content, output_language),
                schema=ResumeEnrichmentAnalysisOutput,
            )
            result = _validate_llm_result(ResumeEnrichmentAnalysisOutput, result)
            result_serializer = AnalysisResultSerializer(data=result)
            result_serializer.is_valid(raise_exception=True)
            return Response(result_serializer.data)
        except Exception:
            logger.exception("Resume enrichment analysis failed for %s", resume.id)
            return Response(
                {"detail": "Failed to analyze resume. Please try again."},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class ResumeEnrichmentEnhanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        resume, error = _get_resume(request, resume_id)
        if error:
            return error
        request_serializer = EnhanceRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        answers = request_serializer.validated_data["answers"]
        details_by_id = _resume_details(resume.content)

        question_to_item = {}
        missing_item_ids = [
            answer
            for answer in answers
            if answer.get("item_id") not in details_by_id
        ]
        if missing_item_ids:
            language = get_language_name(request.data.get("output_language", "en"))
            try:
                analysis = generate_structured_output(
                    system_prompt="You are a truthful resume analyst. Return only JSON.",
                    user_prompt=_analysis_prompt(resume.content, language),
                    schema=ResumeEnrichmentAnalysisOutput,
                )
                analysis = _validate_llm_result(
                    ResumeEnrichmentAnalysisOutput, analysis
                )
            except Exception:
                logger.exception("Resume re-analysis failed for %s", resume.id)
                return Response(
                    {"detail": "Failed to match answers to resume items."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            question_to_item = {
                question["question_id"]: question["item_id"]
                for question in analysis["questions"]
            }
            for item in analysis["items_to_enrich"]:
                details_by_id[item["item_id"]] = item

        grouped_answers = {}
        for answer in answers:
            item_id = answer.get("item_id") or question_to_item.get(
                answer["question_id"], ""
            )
            if item_id in details_by_id:
                grouped_answers.setdefault(item_id, []).append(answer)

        language = get_language_name(request.data.get("output_language", "en"))
        previews = []
        errors = []
        for item_id, item_answers in grouped_answers.items():
            item = details_by_id[item_id]
            answers_text = "\n\n".join(
                f"Q: {answer.get('question_text') or answer['question_id']}\n"
                f"A: {answer['answer']}"
                for answer in item_answers
            )
            current_description = item.get("current_description", [])
            prompt = ENHANCE_DESCRIPTION_PROMPT.format(
                output_language=language,
                item_type=item["item_type"],
                title=item.get("title", ""),
                subtitle=item.get("subtitle", ""),
                current_description=(
                    "\n".join(f"- {line}" for line in current_description)
                    or "(No description)"
                ),
                answers=answers_text,
            )
            try:
                generated = generate_structured_output(
                    system_prompt="You are a truthful resume writer. Use only candidate-provided facts.",
                    user_prompt=prompt,
                    schema=EnhancedBulletsOutput,
                )
                generated = _validate_llm_result(EnhancedBulletsOutput, generated)
                previews.append(
                    {
                        "item_id": item_id,
                        "item_type": item["item_type"],
                        "title": item.get("title", ""),
                        "original_description": current_description,
                        "enhanced_description": generated["additional_bullets"],
                    }
                )
            except Exception:
                logger.exception("Enhancement generation failed for %s", item_id)
                errors.append(
                    {
                        "item_id": item_id,
                        "item_type": item["item_type"],
                        "title": item.get("title", ""),
                        "subtitle": item.get("subtitle", ""),
                        "message": "Failed to enhance this item. Please try again.",
                    }
                )

        if not previews:
            return Response(
                {"detail": "No enhancements could be generated.", "errors": errors},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        result = {"enhancements": previews, "errors": errors}
        response_serializer = EnhancementPreviewSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data)


class ResumeEnrichmentApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        resume, error = _get_resume(request, resume_id)
        if error:
            return error
        request_serializer = ApplyEnhancementsRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        content = json.loads(json.dumps(resume.content or {}))
        details_by_id = _resume_details(content)

        for enhancement in request_serializer.validated_data["enhancements"]:
            item_id = enhancement["item_id"]
            current = details_by_id.get(item_id)
            if (
                current is None
                or current["item_type"] != enhancement["item_type"]
                or current["current_description"]
                != enhancement["original_description"]
            ):
                return Response(
                    {"detail": "Resume content changed. Generate a new preview before applying."},
                    status=status.HTTP_409_CONFLICT,
                )

            match = re.fullmatch(r"(exp|proj)_(\d+)", item_id)
            if not match:
                return Response(
                    {"detail": "Invalid resume item identifier."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            section = "experience" if match.group(1) == "exp" else "projects"
            item = content[section][int(match.group(2))]
            bullets = _description_list(item.get("bullets"))
            seen = {bullet.casefold() for bullet in bullets}
            bullets.extend(
                bullet
                for bullet in enhancement["enhanced_description"]
                if bullet.casefold() not in seen
            )
            item["bullets"] = bullets

        return _save_enriched_content(resume, content)


class ResumeEnrichmentRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        resume, error = _get_resume(request, resume_id)
        if error:
            return error
        request_serializer = RegenerateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        instruction = request_serializer.validated_data["instruction"].strip()
        if not instruction:
            raise serializers.ValidationError(
                {"instruction": "This field may not be blank."}
            )
        output_language = get_language_name(
            request_serializer.validated_data.get("output_language", "en")
        )

        regenerated_items = []
        errors = []
        for item in request_serializer.validated_data["items"]:
            try:
                if item["item_type"] == "skills":
                    prompt = REGENERATE_SKILLS_PROMPT.format(
                        output_language=output_language,
                        current_skills=", ".join(item["current_content"]),
                        user_instruction=instruction,
                    )
                    result = generate_structured_output(
                        system_prompt="You are a truthful resume writer.",
                        user_prompt=prompt,
                        schema=RegeneratedSkillsOutput,
                    )
                    result = _validate_llm_result(RegeneratedSkillsOutput, result)
                    new_content = result["new_skills"]
                else:
                    prompt = REGENERATE_ITEM_PROMPT.format(
                        output_language=output_language,
                        item_type=item["item_type"],
                        title=item["title"],
                        subtitle=item["subtitle"],
                        current_description="\n".join(
                            f"- {line}" for line in item["current_content"]
                        )
                        or "(No description)",
                        user_instruction=instruction,
                    )
                    result = generate_structured_output(
                        system_prompt="You are a truthful resume writer.",
                        user_prompt=prompt,
                        schema=RegeneratedBulletsOutput,
                    )
                    result = _validate_llm_result(RegeneratedBulletsOutput, result)
                    new_content = result["new_bullets"]

                regenerated_items.append(
                    {
                        **item,
                        "original_content": item["current_content"],
                        "new_content": new_content,
                        "diff_summary": result.get("change_summary", ""),
                    }
                )
            except Exception:
                logger.exception("Failed to regenerate item %s", item["item_id"])
                errors.append(
                    {
                        "item_id": item["item_id"],
                        "item_type": item["item_type"],
                        "title": item["title"],
                        "subtitle": item["subtitle"],
                        "message": "Failed to regenerate this item. Please try again.",
                    }
                )

        if not regenerated_items:
            return Response(
                {"detail": "Failed to regenerate content.", "errors": errors},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        result = {"regenerated_items": regenerated_items, "errors": errors}
        response_serializer = RegenerateResponseSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data)


class ResumeEnrichmentApplyRegeneratedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):
        resume, error = _get_resume(request, resume_id)
        if error:
            return error
        request_serializer = ApplyRegeneratedRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        content = json.loads(json.dumps(resume.content or {}))
        details_by_id = _resume_details(content)

        for replacement in request_serializer.validated_data["regenerated_items"]:
            item_id = replacement["item_id"]
            item_type = replacement["item_type"]
            if item_type == "skills":
                category = replacement["title"]
                skills = content.get("skills", {})
                if (
                    not category
                    or not isinstance(skills, dict)
                    or _description_list(skills.get(category))
                    != replacement["original_content"]
                ):
                    return Response(
                        {"detail": "Resume skills changed. Generate a new preview before applying."},
                        status=status.HTTP_409_CONFLICT,
                    )
                skills[category] = replacement["new_content"]
                continue

            current = details_by_id.get(item_id)
            if (
                current is None
                or current["item_type"] != item_type
                or current["current_description"]
                != replacement["original_content"]
            ):
                return Response(
                    {"detail": "Resume content changed. Generate a new preview before applying."},
                    status=status.HTTP_409_CONFLICT,
                )

            match = re.fullmatch(r"(exp|proj)_(\d+)", item_id)
            if not match:
                return Response(
                    {"detail": "Invalid resume item identifier."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            section = "experience" if match.group(1) == "exp" else "projects"
            item = content[section][int(match.group(2))]
            if section == "experience":
                item["bullets"] = replacement["new_content"]
            elif _description_list(item.get("description")):
                item["description"] = replacement["new_content"][0]
                item["bullets"] = replacement["new_content"][1:]
            else:
                item["bullets"] = replacement["new_content"]

        return _save_enriched_content(resume, content)