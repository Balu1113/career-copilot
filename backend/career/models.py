from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
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


class CareerRoadmap(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="career_roadmaps",
    )

    career_analysis = models.ForeignKey(
        "CareerAnalysis",
        on_delete=models.CASCADE,
        related_name="roadmaps",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255)

    target_role = models.CharField(
        max_length=255,
        blank=True,
    )

    roadmap_data = models.JSONField(
        default=dict,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user}"


class InterviewSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )

    career_analysis = models.ForeignKey(
        "CareerAnalysis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interview_sessions",
    )

    target_role = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    interview_type = models.CharField(
        max_length=50,
        default="mixed",
    )

    questions = models.JSONField(
        default=list,
    )

    current_question_index = models.PositiveIntegerField(
        default=0,
    )

    completed = models.BooleanField(
        default=False,
    )

    overall_score = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"Interview #{self.id}"
        )


class InterviewResponse(models.Model):
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="responses",
    )

    question_index = models.PositiveIntegerField()

    question = models.TextField()

    category = models.CharField(
        max_length=50,
    )

    difficulty = models.CharField(
        max_length=50,
    )

    answer = models.TextField()

    evaluation = models.JSONField(
        default=dict,
    )

    score = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["question_index"]
        unique_together = [
            ("session", "question_index"),
        ]

    def __str__(self):
        return (
            f"Interview #{self.session_id} - "
            f"Question {self.question_index + 1}"
        )