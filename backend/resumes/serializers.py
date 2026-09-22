from rest_framework import serializers

from rag.services.vector_store import create_resume_vector_store

from .models import Resume, ResumeIntelligence
from .services.parser import extract_resume_text
from .services.resume_intelligence import generate_resume_intelligence


class ResumeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resume
        fields = [
            "id",
            "title",
            "file",
            "uploaded_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "uploaded_at",
            "updated_at",
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

    def create(self, validated_data):
        resume = Resume.objects.create(**validated_data)

        try:
            resume.file.open("rb")

            resume.extracted_text = extract_resume_text(
                resume.file
            )

            resume.save(
                update_fields=["extracted_text"]
            )

        finally:
            resume.file.close()

        # Create FAISS vector store for RAG
        create_resume_vector_store(resume)

        # Generate and save Resume Intelligence
        try:
            intelligence = generate_resume_intelligence(
                resume.extracted_text
            )

            ResumeIntelligence.objects.update_or_create(
                resume=resume,
                defaults=intelligence.model_dump(),
            )

        except Exception as exc:
            print(
                f"Resume intelligence generation failed "
                f"for resume {resume.id}: {exc}"
            )

        return resume


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