from rest_framework import serializers


WIZARD_SECTIONS = (
    "intro",
    "contact",
    "summary",
    "workExperience",
    "internships",
    "education",
    "personalProjects",
    "skills",
    "review",
)


class ResumeWizardAnswerSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=True)


class ResumeWizardTurnRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=("start", "answer", "skip", "back", "review")
    )
    state = serializers.JSONField(required=False)
    answer = ResumeWizardAnswerSerializer(required=False, allow_null=True)
    output_language = serializers.CharField(required=False, default="en")


class ResumeWizardTurnResponseSerializer(serializers.Serializer):
    state = serializers.JSONField()


class ResumeWizardFinalizeRequestSerializer(serializers.Serializer):
    state = serializers.JSONField()


class ResumeWizardFinalizeResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    request_id = serializers.UUIDField()
    resume_id = serializers.IntegerField()
    processing_status = serializers.ChoiceField(choices=("ready",))
    is_master = serializers.BooleanField()