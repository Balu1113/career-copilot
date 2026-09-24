from django.urls import path

from .views import (
    CareerAnalysisStreamView,
    InterviewPrepView,
    CareerAnalysisHistoryView,
    CareerAnalysisHistoryDetailView,
    CareerDashboardView,
    InterviewAnswerEvaluationView,
)
urlpatterns = [

    path(
        "interview-prep/",
        InterviewPrepView.as_view(),
        name="interview-prep",
    ),

    path(
        "analyze-stream/",
        CareerAnalysisStreamView.as_view(),
        name="career-analysis-stream",
    ),

    path(
    "history/",
    CareerAnalysisHistoryView.as_view(),
    ),

    path(
        "history/<int:pk>/",
        CareerAnalysisHistoryDetailView.as_view(),
    ),

    path(
        "dashboard/",
        CareerDashboardView.as_view(),
        name="career-dashboard",
    ),

    path(
        "interview/evaluate/",
        InterviewAnswerEvaluationView.as_view(),
        name="interview-answer-evaluate",
    ),
]