from rest_framework import serializers

from .models import LearnSession


class LearnSessionCreateSerializer(serializers.Serializer):
    level = serializers.ChoiceField(
        choices=[
            "beginner",
            "intermediate",
            "advanced",
        ],
        required=False,
        default="beginner",
    )


class LearnMessageSerializer(serializers.Serializer):
    content = serializers.CharField(
        required=True,
        allow_blank=False,
    )
