from django.conf import settings
from django.db import models


class LearnSession(models.Model):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learn_sessions",
    )

    title = models.CharField(
        max_length=255,
        blank=True,
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="beginner",
    )

    messages = models.JSONField(
        default=list,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title or 'New chat'} - {self.user}"
