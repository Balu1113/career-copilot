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

    # Structured resume JSON (personalInfo/workExperience/... schema).
    processed_data = models.JSONField(null=True, blank=True)

    # Editable builder content (personal/summary/skills/experience/...)
    # saved when this uploaded resume is edited in the Resume Editor.
    builder_content = models.JSONField(null=True, blank=True, default=None)

    # "md" for source text parsed from an upload, "json" for structured data.
    content_type = models.CharField(max_length=10, default="md")

    # Snapshot of the source text captured at upload time.
    original_markdown = models.TextField(blank=True, default="")

    cover_letter = models.TextField(blank=True, default="")

    outreach_message = models.TextField(blank=True, default="")

    interview_prep = models.JSONField(null=True, blank=True)

    # First resume uploaded by a user becomes the master resume.
    is_master = models.BooleanField(default=False)

    # Set on tailored resumes: the resume and job they came from.
    source_resume = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tailored_resumes",
    )

    job = models.ForeignKey(
        "jobs.JobPosting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tailored_resumes",
    )

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


class ResumePreview(models.Model):
    """Registered improve/preview result with claim/lease replay semantics."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resume_previews",
    )

    source_resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="previews",
    )

    job = models.ForeignKey(
        "jobs.JobPosting",
        on_delete=models.CASCADE,
        related_name="resume_previews",
    )

    payload_hash = models.CharField(max_length=64)
    source_hash = models.CharField(max_length=64)
    job_hash = models.CharField(max_length=64)
    prompt_id = models.CharField(max_length=64, blank=True, default="")

    improvements = models.JSONField(default=list)

    # Populated once the preview is confirmed (durable replay payload).
    response = models.JSONField(null=True, blank=True)

    # Claim/lease state.
    token = models.CharField(max_length=64, blank=True, default="")
    claimed_at = models.DateTimeField(null=True, blank=True)

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source_resume", "job", "expires_at"]),
        ]

    def __str__(self):
        return f"Preview {self.pk} - resume {self.source_resume_id}"