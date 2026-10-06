import time

from django.core.management.base import BaseCommand

from resumes.services.resume_jobs import (
    MAX_ATTEMPTS,
    claim_next_job,
    execute_job,
)


def process_next_job(max_attempts=MAX_ATTEMPTS):
    claim = claim_next_job()

    if claim is None:
        return False

    execute_job(claim, max_attempts=max_attempts)
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
