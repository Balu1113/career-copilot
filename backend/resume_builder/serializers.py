from pathlib import Path

from rest_framework import serializers

from .models import (
    ResumeTemplate,
    GeneratedResume,
)
from .services.template_analyzer import analyze_template


class ResumeTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeTemplate
        fields = [
            "id",
            "name",
            "sample_file",
            "file_type",
            "template_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "file_type",
            "template_data",
            "created_at",
            "updated_at",
        ]

    def validate_sample_file(self, value):
        extension = Path(value.name).suffix.lower()

        if extension not in {".docx", ".pdf"}:
            raise serializers.ValidationError(
                "Only PDF and DOCX sample resumes are supported."
            )

        return value

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