from rag.services.vector_store import create_resume_vector_store
from ..models import Resume, ResumeIntelligence
from .resume_intelligence import generate_resume_intelligence


def process_resume_ai(resume_id):
    print(
        f"[RESUME PROCESSING] Starting resume {resume_id}",
        flush=True,
    )

    try:
        resume = Resume.objects.get(id=resume_id)

        resume.processing_status = "processing"
        resume.processing_error = ""
        resume.save(
            update_fields=[
                "processing_status",
                "processing_error",
            ]
        )

        print(
            f"[RESUME PROCESSING] Resume {resume_id}: "
            f"creating vector store...",
            flush=True,
        )

        create_resume_vector_store(resume)

        print(
            f"[RESUME PROCESSING] Resume {resume_id}: "
            f"vector store completed.",
            flush=True,
        )

        print(
            f"[RESUME PROCESSING] Resume {resume_id}: "
            f"generating resume intelligence...",
            flush=True,
        )

        intelligence = generate_resume_intelligence(
            resume.extracted_text
        )

        print(
            f"[RESUME PROCESSING] Resume {resume_id}: "
            f"resume intelligence completed.",
            flush=True,
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

        print(
            f"[RESUME PROCESSING] Resume {resume_id}: "
            f"COMPLETED",
            flush=True,
        )

    except Exception as exc:
        try:
            resume = Resume.objects.get(id=resume_id)

            resume.processing_status = "failed"
            resume.processing_error = str(exc)

            resume.save(
                update_fields=[
                    "processing_status",
                    "processing_error",
                ]
            )
        except Exception as save_error:
            print(
                f"[RESUME PROCESSING] Failed to save error "
                f"status for resume {resume_id}: {save_error}",
                flush=True,
            )

        print(
            f"[RESUME PROCESSING] Resume {resume_id}: "
            f"FAILED: {exc}",
            flush=True,
        )