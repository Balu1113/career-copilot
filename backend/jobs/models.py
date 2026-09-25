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