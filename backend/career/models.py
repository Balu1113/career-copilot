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
        on_delete=models.CASCADE,
        related_name="career_analyses",
    )

    job_description = models.TextField()

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

    resume_intelligence = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"Career Analysis #{self.id}"
        )