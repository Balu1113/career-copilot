from django.urls import path

from .views import (
    CareerAnalysisView,
    CareerAnalysisStreamView,
    InterviewPrepView,
    CareerAnalysisHistoryView,
    CareerAnalysisHistoryDetailView,
)
urlpatterns = [
    path(
        "analyze/",
        CareerAnalysisView.as_view(),
        name="career-analysis",
    ),

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


]