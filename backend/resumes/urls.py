from django.urls import path

from .views import (
    ResumeDetailView,
    ResumeDownloadView,
    ResumeListCreateView,
    SetActiveResumeView,
    ResumeIntelligenceView,
    GenerateResumeIntelligenceView,
)


urlpatterns = [
    path(
        "",
        ResumeListCreateView.as_view(),
        name="resume-list-create",
    ),

    path(
        "<int:pk>/",
        ResumeDetailView.as_view(),
        name="resume-detail",
    ),

    path(
        "<int:pk>/download/",
        ResumeDownloadView.as_view(),
        name="resume-download",
    ),

    path(
        "<int:pk>/activate/",
        SetActiveResumeView.as_view(),
        name="resume-activate",
    ),

    path(
        "<int:pk>/intelligence/",
        ResumeIntelligenceView.as_view(),
    ),

    path(
        "<int:pk>/intelligence/generate/",
        GenerateResumeIntelligenceView.as_view(),
    ),
]