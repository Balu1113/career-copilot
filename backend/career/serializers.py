from rest_framework import serializers

from .models import CareerAnalysis


class CareerAnalysisSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()

    job_description = serializers.CharField(
        min_length=50,
        allow_blank=False,
        trim_whitespace=True,
    )

    def validate_job_description(self, value):
        value = value.strip()

        if len(value) < 50:
            raise serializers.ValidationError(
                "Job description must contain at least 50 characters."
            )

        return value


class InterviewPrepSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()

    job_description = serializers.CharField(
        min_length=50
    )


class CareerAnalysisHistorySerializer(
    serializers.ModelSerializer
):
    resume_title = serializers.CharField(
        source="resume.title",
        read_only=True,
    )

    class Meta:
        model = CareerAnalysis

        fields = [
            "id",
            "resume",
            "resume_title",
            "job_description",
            "resume_intelligence",
            "job_requirements",
            "resume_analysis",
            "skill_gap_analysis",
            "career_recommendation",
            "interview_preparation",
            "created_at",
        ]

        read_only_fields = fields


class InterviewAnswerEvaluationSerializer(
    serializers.Serializer
):
    analysis_id = serializers.IntegerField()

    question = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    category = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    difficulty = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    answer = serializers.CharField(
        min_length=10,
        allow_blank=False,
        trim_whitespace=True,
    )