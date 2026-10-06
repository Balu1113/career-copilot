from rest_framework import serializers


class EnrichmentQuestionSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    item_id = serializers.CharField()
    question = serializers.CharField()
    placeholder = serializers.CharField(allow_blank=True, required=False, default="")


class EnrichmentItemSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    item_type = serializers.ChoiceField(choices=("experience", "project"))
    title = serializers.CharField(allow_blank=True, required=False, default="")
    subtitle = serializers.CharField(allow_blank=True, required=False, default="")
    current_description = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    weakness_reason = serializers.CharField(allow_blank=True, required=False, default="")


class AnalysisResultSerializer(serializers.Serializer):
    items_to_enrich = EnrichmentItemSerializer(many=True)
    questions = EnrichmentQuestionSerializer(many=True, max_length=6)
    analysis_summary = serializers.CharField(allow_blank=True, required=False, default="")


class AnswerInputSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    item_id = serializers.CharField(required=False, allow_blank=True, default="")
    question_text = serializers.CharField(required=False, allow_blank=True, default="")
    answer = serializers.CharField()


class EnhanceRequestSerializer(serializers.Serializer):
    answers = AnswerInputSerializer(many=True, allow_empty=False, max_length=6)


class EnhancedItemSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    item_type = serializers.ChoiceField(choices=("experience", "project"))
    title = serializers.CharField(allow_blank=True)
    original_description = serializers.ListField(child=serializers.CharField())
    enhanced_description = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )


class EnhancementErrorSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    item_type = serializers.CharField()
    title = serializers.CharField(allow_blank=True)
    subtitle = serializers.CharField(allow_blank=True, required=False, default="")
    message = serializers.CharField()


class EnhancementPreviewSerializer(serializers.Serializer):
    enhancements = EnhancedItemSerializer(many=True)
    errors = EnhancementErrorSerializer(many=True, required=False, default=list)


class ApplyEnhancementsRequestSerializer(serializers.Serializer):
    enhancements = EnhancedItemSerializer(many=True, allow_empty=False, max_length=6)


class RegenerateItemInputSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    item_type = serializers.ChoiceField(choices=("experience", "project", "skills"))
    title = serializers.CharField(allow_blank=True, required=False, default="")
    subtitle = serializers.CharField(allow_blank=True, required=False, default="")
    current_content = serializers.ListField(child=serializers.CharField())


class RegenerateRequestSerializer(serializers.Serializer):
    instruction = serializers.CharField()
    output_language = serializers.CharField(required=False, default="en")
    items = RegenerateItemInputSerializer(many=True, allow_empty=False, max_length=6)


class RegeneratedItemSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    item_type = serializers.ChoiceField(choices=("experience", "project", "skills"))
    title = serializers.CharField(allow_blank=True, required=False, default="")
    subtitle = serializers.CharField(allow_blank=True, required=False, default="")
    original_content = serializers.ListField(child=serializers.CharField())
    new_content = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    diff_summary = serializers.CharField(allow_blank=True, required=False, default="")


class RegenerateErrorSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    item_type = serializers.CharField()
    title = serializers.CharField(allow_blank=True)
    subtitle = serializers.CharField(allow_blank=True, required=False, default="")
    message = serializers.CharField()


class RegenerateResponseSerializer(serializers.Serializer):
    regenerated_items = RegeneratedItemSerializer(many=True)
    errors = RegenerateErrorSerializer(many=True, required=False, default=list)


class ApplyRegeneratedRequestSerializer(serializers.Serializer):
    regenerated_items = RegeneratedItemSerializer(
        many=True, allow_empty=False, max_length=6
    )