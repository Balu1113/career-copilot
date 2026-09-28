import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from resumes.models import Resume, ResumeProcessingJob
from resumes.services.resume_processing import process_resume_ai


def process_next_job(max_attempts=3):
    now = timezone.now()
    stale_before = now - timedelta(minutes=15)

    with transaction.atomic():
        job = (
            ResumeProcessingJob.objects
            .select_for_update()
            .filter(
                Q(
                    status=ResumeProcessingJob.STATUS_PENDING,
                    available_at__lte=now,
                )
                | Q(
                    status=ResumeProcessingJob.STATUS_PROCESSING,
                    updated_at__lt=stale_before,
                )
            )
            .order_by("created_at")
            .first()
        )

        if job is None:
            return False

        job.status = ResumeProcessingJob.STATUS_PROCESSING
        job.attempts += 1
        job.last_error = ""
        job.save(update_fields=["status", "attempts", "last_error", "updated_at"])
        job_id = job.id
        resume_id = job.resume_id
        attempts = job.attempts

    try:
        process_resume_ai(resume_id)
        resume = Resume.objects.get(id=resume_id)
        if resume.processing_status != "completed":
            raise RuntimeError(
                resume.processing_error or "Resume processing did not complete."
            )
    except Exception as exc:
        job = ResumeProcessingJob.objects.get(id=job_id)
        job.status = (
            ResumeProcessingJob.STATUS_FAILED
            if attempts >= max_attempts
            else ResumeProcessingJob.STATUS_PENDING
        )
        job.available_at = timezone.now() + timedelta(
            seconds=30 * (2 ** attempts)
        )
        job.last_error = str(exc)[:4000]
        job.save(
            update_fields=["status", "available_at", "last_error", "updated_at"]
        )
        Resume.objects.filter(id=resume_id).update(
            processing_status=job.status,
            processing_error=job.last_error,
        )
    else:
        ResumeProcessingJob.objects.filter(id=job_id).update(
            status=ResumeProcessingJob.STATUS_COMPLETED,
            last_error="",
            updated_at=timezone.now(),
        )

    return True


class Command(BaseCommand):
    help = "Process queued resume extraction and AI jobs."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--poll-interval", type=float, default=2.0)
        parser.add_argument("--max-attempts", type=int, default=3)

    def handle(self, *args, **options):
        while True:
            worked = process_next_job(options["max_attempts"])
            if options["once"]:
                return
            if not worked:
                time.sleep(max(0.2, options["poll_interval"]))