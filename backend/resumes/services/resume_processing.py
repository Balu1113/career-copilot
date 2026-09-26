from rag.services.vector_store import create_resume_vector_store

from ..models import Resume, ResumeIntelligence
from .resume_intelligence import generate_resume_intelligence


def process_resume_ai(resume_id):
    resume = Resume.objects.get(id=resume_id)

    try:
        resume.processing_status = "processing"
        resume.processing_error = ""
        resume.save(
            update_fields=[
                "processing_status",
                "processing_error",
            ]
        )

        # Create FAISS vector store for RAG
        create_resume_vector_store(resume)

        # Generate Resume Intelligence
        intelligence = generate_resume_intelligence(
            resume.extracted_text
        )

        ResumeIntelligence.objects.update_or_create(
            resume=resume,
            defaults=intelligence.model_dump(),
        )

        resume.processing_status = "completed"
        resume.processing_error = ""
        resume.save(
            update_fields=[
                "processing_status",
                "processing_error",
            ]
        )

    except Exception as exc:
        resume.processing_status = "failed"
        resume.processing_error = str(exc)

        resume.save(
            update_fields=[
                "processing_status",
                "processing_error",
            ]
        )

        print(
            f"Resume AI processing failed "
            f"for resume {resume.id}: {exc}"
        )