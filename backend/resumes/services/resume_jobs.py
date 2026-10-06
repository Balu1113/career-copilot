"""Queue helpers for resume AI processing.

A job is enqueued when a resume is uploaded. It is executed either by
the ``process_resume_jobs`` worker (Docker) or by an in-process
background thread (local dev / single server) so the user never waits
on a queue that nobody is draining.

Claiming uses an atomic UPDATE so a worker and an in-process thread can
never run the same job twice.
"""

import threading
from datetime import timedelta

from django.db import close_old_connections
from django.db.models import F, Q
from django.utils import timezone

from ..models import Resume, ResumeProcessingJob
from .resume_processing import process_resume_ai

STALE_AFTER = timedelta(minutes=15)
MAX_ATTEMPTS = 3


def _due_q(now):
    return (
        Q(
            status=ResumeProcessingJob.STATUS_PENDING,
            available_at__lte=now,
        )
        | Q(
            status=ResumeProcessingJob.STATUS_PROCESSING,
            updated_at__lt=now - STALE_AFTER,
        )
    )


def claim_job(job_id):
    """Atomically claim one job. Returns a claim dict, or None."""
    now = timezone.now()

    claimed = (
        ResumeProcessingJob.objects.filter(id=job_id)
        .filter(_due_q(now))
        .update(
            status=ResumeProcessingJob.STATUS_PROCESSING,
            updated_at=now,
            last_error="",
            attempts=F("attempts") + 1,
        )
    )

    if not claimed:
        return None

    job = ResumeProcessingJob.objects.get(id=job_id)

    return {
        "job_id": job.id,
        "resume_id": job.resume_id,
        "attempts": job.attempts,
    }


def claim_next_job():
    """Claim the oldest due job in the queue, or None."""
    now = timezone.now()

    candidate_ids = list(
        ResumeProcessingJob.objects.filter(_due_q(now))
        .order_by("created_at")
        .values_list("id", flat=True)[:5]
    )

    for job_id in candidate_ids:
        claim = claim_job(job_id)
        if claim:
            return claim

    return None


def execute_job(claim, max_attempts=MAX_ATTEMPTS):
    """Run a claimed job and record completed/pending/failed state."""
    job_id = claim["job_id"]
    resume_id = claim["resume_id"]
    attempts = claim["attempts"]

    try:
        process_resume_ai(resume_id)

        resume = Resume.objects.get(id=resume_id)

        if resume.processing_status != "completed":
            raise RuntimeError(
                resume.processing_error
                or "Resume processing did not complete."
            )

    except Exception as exc:
        now = timezone.now()
        failed = attempts >= max_attempts

        job = ResumeProcessingJob.objects.get(id=job_id)
        job.status = (
            ResumeProcessingJob.STATUS_FAILED
            if failed
            else ResumeProcessingJob.STATUS_PENDING
        )
        job.available_at = now + timedelta(
            seconds=30 * (2 ** attempts)
        )
        job.last_error = str(exc)[:4000]
        job.save(
            update_fields=[
                "status",
                "available_at",
                "last_error",
                "updated_at",
            ]
        )

        # process_resume_ai already set the resume to "failed";
        # requeue it as "pending" while retries remain.
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

    return False


def run_job(job_id, max_attempts=MAX_ATTEMPTS):
    """Claim and execute a specific job. Returns True if it ran."""
    claim = claim_job(job_id)
    if claim is None:
        return False

    execute_job(claim, max_attempts=max_attempts)
    return True


def _run_job_thread(job_id):
    close_old_connections()
    try:
        run_job(job_id)
    except Exception as exc:  # pragma: no cover - defensive
        ResumeProcessingJob.objects.filter(id=job_id).update(
            last_error=str(exc)[:4000],
        )
    finally:
        close_old_connections()


def _spawn(job_id, run_async):
    if run_async:
        threading.Thread(
            target=_run_job_thread,
            args=(job_id,),
            daemon=True,
        ).start()
    else:
        _run_job_thread(job_id)


def schedule_resume_processing(resume, run_async=True):
    """Ensure a job exists for the resume and start processing it."""
    job, _ = ResumeProcessingJob.objects.get_or_create(
        resume=resume
    )
    _spawn(job.id, run_async)
    return job


def reset_and_schedule(resume, run_async=True):
    """User-triggered retry: reset the job and run it again."""
    job, _ = ResumeProcessingJob.objects.get_or_create(
        resume=resume
    )

    ResumeProcessingJob.objects.filter(id=job.id).update(
        status=ResumeProcessingJob.STATUS_PENDING,
        attempts=0,
        available_at=timezone.now(),
        last_error="",
        updated_at=timezone.now(),
    )

    Resume.objects.filter(id=resume.id).update(
        processing_status="pending",
        processing_error="",
    )

    _spawn(job.id, run_async)
    return job


def schedule_stuck_resumes(resumes):
    """
    Kick processing for resumes that are stuck in pending/processing.

    This self-heals rows that were queued before the worker existed,
    retries whose backoff window has passed, and jobs orphaned by a
    server restart.  Only claimable jobs get a thread spawned, so the
    frontend's 3s polling does not create thread churn, and
    ``claim_job`` makes duplicate spawns harmless.
    """
    stuck = [
        resume.id
        for resume in resumes
        if resume.processing_status in ("pending", "processing")
    ]

    if not stuck:
        return 0

    jobs_by_resume = {
        job.resume_id: job.id
        for job in ResumeProcessingJob.objects.filter(
            resume_id__in=stuck
        )
    }

    due_resumes = set(
        ResumeProcessingJob.objects.filter(
            resume_id__in=stuck
        )
        .filter(_due_q(timezone.now()))
        .values_list("resume_id", flat=True)
    )

    spawned = 0

    for resume_id in stuck:
        job_id = jobs_by_resume.get(resume_id)

        if job_id is None:
            job_id = ResumeProcessingJob.objects.create(
                resume_id=resume_id
            ).id
        elif resume_id not in due_resumes:
            # Queued but not due yet (backoff) or already running.
            continue

        threading.Thread(
            target=_run_job_thread,
            args=(job_id,),
            daemon=True,
        ).start()
        spawned += 1

    return spawned
