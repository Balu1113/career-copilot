from django.conf import settings
from django.db import models


class ResumeProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resume_profile",
    )

    personal = models.JSONField(default=dict, blank=True)
    experience = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Resume Profile"


class ResumeTemplate(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resume_templates",
    )

    name = models.CharField(max_length=150)

    sample_file = models.FileField(
        upload_to="resume_templates/%Y/%m/"
    )

    file_type = models.CharField(
        max_length=10,
        blank=True,
    )

    # Stores extracted design information later.
    # Example:
    # {
    #     "font": "Calibri",
    #     "body_size": 10,
    #     "heading_size": 14,
    #     "margin_left": 0.6,
    #     "margin_right": 0.6,
    #     "section_spacing": 8,
    #     "layout": "single_column"
    # }
    template_data = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class GeneratedResume(models.Model):
    MODE_BUILDER = "builder"
    MODE_MODIFIER = "modifier"

    MODE_CHOICES = [
        (MODE_BUILDER, "Resume Builder"),
        (MODE_MODIFIER, "Resume Modifier"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_GENERATING = "generating"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_GENERATING, "Generating"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generated_resumes",
    )

    template = models.ForeignKey(
        ResumeTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_resumes",
    )

    source_resume = models.ForeignKey(
        "resumes.Resume",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_versions",
    )

    title = models.CharField(
        max_length=150
    )

    mode = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default=MODE_BUILDER,
    )

    job_description = models.TextField(
        blank=True
    )

    # Resume content will be stored separately from
    # template/design information.
    content = models.JSONField(
        default=dict,
        blank=True,
    )

    output_file = models.FileField(
        upload_to="generated_resumes/%Y/%m/",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    error_message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title