from django.urls import path

from .views import (
    ResumeContentView,
    ResumeContentAIEditView,
    ResumeDetailView,
    ResumeDownloadView,
    ResumeEditedDownloadView,
    ResumeListCreateView,
    ResumeProcessView,
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
        "<int:pk>/content/",
        ResumeContentView.as_view(),
        name="resume-content",
    ),

    path(
        "<int:pk>/content/ai-edit/",
        ResumeContentAIEditView.as_view(),
        name="resume-content-ai-edit",
    ),

    path(
        "<int:pk>/content/download/",
        ResumeEditedDownloadView.as_view(),
        name="resume-content-download",
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
        "<int:pk>/process/",
        ResumeProcessView.as_view(),
        name="resume-process",
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