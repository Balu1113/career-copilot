from django.contrib.auth.models import User
from django.db import models

from resumes.models import Resume


class CareerAnalysis(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="career_analyses",
    )

    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="career_analyses",
    )

    # Snapshot of the analyzed resume title. Uploaded resumes
    # keep their linked resume title; generated resumes store
    # their own title because they are not a Resume record.
    resume_title = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    # Snapshot of the resume text used for the analysis so
    # interview evaluation works even when the linked resume
    # is removed or the analysis came from a generated resume.
    resume_context = models.TextField(
        blank=True,
        default="",
    )

    job_description = models.TextField()

    resume_intelligence = models.JSONField(
        default=dict,
    )

    job_requirements = models.JSONField(
        default=dict,
    )

    resume_analysis = models.JSONField(
        default=dict,
    )

    skill_gap_analysis = models.JSONField(
        default=dict,
    )

    career_recommendation = models.JSONField(
        default=dict,
    )

    interview_preparation = models.JSONField(
        default=dict,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"Career Analysis #{self.id}"
        )