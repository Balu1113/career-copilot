from pathlib import Path

from django.urls import reverse
from rest_framework import serializers

from .models import (
    ResumeTemplate,
    GeneratedResume,
)
from .services.template_analyzer import analyze_template


class ResumeTemplateSerializer(serializers.ModelSerializer):
    sample_file = serializers.FileField(write_only=True, required=False)
    sample_file_url = serializers.SerializerMethodField()

    class Meta:
        model = ResumeTemplate
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_builtin",
            "ats_score",
            "sample_file",
            "sample_file_url",
            "file_type",
            "template_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "description",
            "is_builtin",
            "ats_score",
            "sample_file_url",
            "file_type",
            "template_data",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if not attrs.get("sample_file"):
            raise serializers.ValidationError(
                {"sample_file": "A sample resume file is required."}
            )

        return attrs

    def validate_sample_file(self, value):
        extension = Path(value.name).suffix.lower()

        if extension not in {".docx", ".pdf"}:
            raise serializers.ValidationError(
                "Only PDF and DOCX sample resumes are supported."
            )

        return value

    def get_sample_file_url(self, template):
        if not template.sample_file:
            return None

        return reverse(
            "resume-template-sample-download",
            kwargs={"template_id": template.id},
        ).removeprefix("/api/")

    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        sample_file = validated_data["sample_file"]

        template = ResumeTemplate.objects.create(
            user=request.user,
            name=validated_data["name"],
            sample_file=sample_file,
            file_type=Path(sample_file.name).suffix.lower().lstrip("."),
        )

        try:
            template_data = analyze_template(
                template.sample_file.path
            )

            template.template_data = template_data
            template.save(
                update_fields=["template_data", "updated_at"]
            )

        except Exception as exc:
            template.delete()

            raise serializers.ValidationError(
                f"Could not analyze the sample resume: {str(exc)}"
            )

        return template


class GeneratedResumeSerializer(serializers.ModelSerializer):
    output_file = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedResume
        fields = [
            "id",
            "title",
            "mode",
            "template",
            "source_resume",
            "job_description",
            "content",
            "output_file",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "output_file",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]

    def validate_template(self, template):
        request = self.context.get("request")

        if template.user != request.user:
            raise serializers.ValidationError(
                "You cannot use this resume template."
            )

        return template

    def validate_source_resume(self, source_resume):
        request = self.context.get("request")

        if source_resume.user != request.user:
            raise serializers.ValidationError(
                "You cannot use this resume."
            )

        return source_resume

    def get_output_file(self, generated_resume):
        if not generated_resume.output_file:
            return None

        return reverse(
            "generated-resume-download",
            kwargs={"resume_id": generated_resume.id},
        ).removeprefix("/api/")