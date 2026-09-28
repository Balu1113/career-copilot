from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Resume(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resumes",
    )

    title = models.CharField(max_length=255)

    file = models.FileField(upload_to="resumes/")

    extracted_text = models.TextField(blank=True)

    processing_status = models.CharField(
    max_length=20,
    choices=[
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ],
    default="pending",
    )

    processing_error = models.TextField(
        blank=True,
        default="",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ResumeIntelligence(models.Model):
    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name="intelligence",
    )

    professional_summary = models.TextField(blank=True)

    skills = models.JSONField(default=list)

    programming_languages = models.JSONField(default=list)

    frameworks = models.JSONField(default=list)

    tools_and_technologies = models.JSONField(default=list)

    ai_ml_technologies = models.JSONField(default=list)

    projects = models.JSONField(default=list)

    experience = models.JSONField(default=list)

    education = models.JSONField(default=list)

    certifications = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Intelligence - {self.resume.title}"


class ResumeProcessingJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name="processing_job",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]