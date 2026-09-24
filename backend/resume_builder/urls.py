from django.urls import path

from .views import (
    GeneratedResumeAIEditView,
    GeneratedResumeDownloadView,
    GeneratedResumeListCreateView,
    GeneratedResumeUpdateView,
    ResumeContentGenerationView,
    ResumeProfileView,
    ResumeSummaryGenerationView,
    ResumeTemplateDetailView,
    ResumeTemplateListCreateView,
    UploadedResumeEditForkView,
)

urlpatterns = [
    path(
        "templates/",
        ResumeTemplateListCreateView.as_view(),
        name="resume-template-list-create",
    ),

    path(
        "templates/<int:template_id>/",
        ResumeTemplateDetailView.as_view(),
        name="resume-template-detail",
    ),

    path(
        "resumes/",
        GeneratedResumeListCreateView.as_view(),
        name="generated-resume-list-create",
    ),

    path(
        "resumes/<int:resume_id>/",
        GeneratedResumeUpdateView.as_view(),
        name="generated-resume-update",
    ),

    path(
        "resumes/<int:resume_id>/ai-edit/",
        GeneratedResumeAIEditView.as_view(),
        name="generated-resume-ai-edit",
    ),

    path(
        "resumes/edit-from-upload/<int:resume_id>/",
        UploadedResumeEditForkView.as_view(),
        name="uploaded-resume-edit-fork",
    ),

    path(
        "resumes/<int:resume_id>/download/",
        GeneratedResumeDownloadView.as_view(),
        name="generated-resume-download",
    ),

    path(
        "generate/",
        ResumeContentGenerationView.as_view(),
        name="resume-content-generate",
    ),

    path(
        "summary/generate/",
        ResumeSummaryGenerationView.as_view(),
        name="resume-summary-generate",
    ),

    path(
        "profile/",
        ResumeProfileView.as_view(),
        name="resume-profile",
    ),
]