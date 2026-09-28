from rest_framework import serializers



from .models import Resume, ResumeIntelligence
class ResumeSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Resume
        fields = [
            "id",
            "title",
            "file",
            "uploaded_at",
            "updated_at",
            "processing_status",
            "processing_error",
        ]
        read_only_fields = [
            "id",
            "uploaded_at",
            "updated_at",
            "processing_status",
            "processing_error",
        ]

    def validate_file(self, value):
        allowed_extensions = [".pdf", ".docx"]

        file_name = value.name.lower()

        if not any(
            file_name.endswith(extension)
            for extension in allowed_extensions
        ):
            raise serializers.ValidationError(
                "Only PDF and DOCX files are allowed."
            )

        return value

class ResumeIntelligenceSerializer(serializers.ModelSerializer):

    resume_id = serializers.IntegerField(
        source="resume.id",
        read_only=True,
    )

    resume_title = serializers.CharField(
        source="resume.title",
        read_only=True,
    )

    class Meta:
        model = ResumeIntelligence

        fields = [
            "resume_id",
            "resume_title",
            "professional_summary",
            "skills",
            "programming_languages",
            "frameworks",
            "tools_and_technologies",
            "ai_ml_technologies",
            "projects",
            "experience",
            "education",
            "certifications",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields