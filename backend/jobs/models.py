from django.contrib.auth.models import User
from django.db import models


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("saved", "Saved"),
        ("applied", "Applied"),
        ("interview", "Interview"),
        ("rejected", "Rejected"),
        ("offer", "Offer"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )

    company = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)

    job_url = models.URLField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="saved",
    )

    applied_date = models.DateField(
        blank=True,
        null=True,
    )

    notes = models.TextField(
        blank=True,
    )
    
    follow_up_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company} - {self.job_title}"


class JobPosting(models.Model):
    """A stored job description used to tailor resumes."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_postings",
    )

    content = models.TextField()

    # Cached from keyword extraction (zero extra LLM calls downstream).
    company = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=255, blank=True, default="")

    job_keywords = models.JSONField(null=True, blank=True)
    job_keywords_hash = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        label = self.role or self.company or f"Job {self.pk}"
        return f"{label} - {self.user.username}"