from django.urls import path

from .views import (
    CareerAnalysisStreamView,
    InterviewPrepView,
    CareerAnalysisHistoryView,
    CareerAnalysisHistoryDetailView,
    CareerDashboardView,
    InterviewAnswerEvaluationView,
    InterviewPerformanceAnalyticsView,
    ResumeOptimizationView,
    CareerRoadmapView,
    CareerRoadmapListView,
    CareerRoadmapDetailView,
    StartInterviewView,
    SubmitInterviewAnswerView,
    InterviewSessionDetailView,
    InterviewHistoryView,
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

    path(
        "optimize-resume/",
        ResumeOptimizationView.as_view(),
        name="optimize-resume",
    ),

    path(
        "roadmap/",
        CareerRoadmapView.as_view(),
        name="career-roadmap",
    ),

    path(
        "roadmaps/",
        CareerRoadmapListView.as_view(),
        name="career-roadmaps",
    ),

    path(
        "roadmaps/<int:roadmap_id>/",
        CareerRoadmapDetailView.as_view(),
        name="career-roadmap-detail",
    ),

    path(
        "interview/analytics/",
        InterviewPerformanceAnalyticsView.as_view(),
        name="interview-performance-analytics",
    ),

    path(
        "interview/start/",
        StartInterviewView.as_view(),
        name="start-interview",
    ),

    path(
        "interview/answer/",
        SubmitInterviewAnswerView.as_view(),
        name="submit-interview-answer",
    ),

    path(
        "interview/sessions/<int:session_id>/",
        InterviewSessionDetailView.as_view(),
        name="interview-session-detail",
    ),

    path(
        "interview/history/",
        InterviewHistoryView.as_view(),
        name="interview-history",
    ),
]