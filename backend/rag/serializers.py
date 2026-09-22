from rest_framework import serializers


class ResumeQuestionSerializer(serializers.Serializer):
    resume_id = serializers.IntegerField()
    question = serializers.CharField()