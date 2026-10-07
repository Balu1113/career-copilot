from django.urls import path

from .enrichment_views import (
    ResumeEnrichmentAnalyzeView,
    ResumeEnrichmentApplyRegeneratedView,
    ResumeEnrichmentApplyView,
    ResumeEnrichmentEnhanceView,
    ResumeEnrichmentRegenerateView,
)
from .resume_wizard_views import (
    ResumeWizardFinalizeView,
    ResumeWizardTurnView,
)
from .views import (
    GeneratedResumeAIEditView,
    GeneratedResumeDownloadView,
    GeneratedResumeListCreateView,
    GeneratedResumeUpdateView,
    ResumeContentGenerationView,
    ResumeProfileView,
    ResumeProjectsGenerationView,
    ResumeSummaryGenerationView,
    ResumeTemplateDetailView,
    ResumeTemplateListCreateView,
    ResumeTemplateSampleDownloadView,
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
        "templates/<int:template_id>/sample/",
        ResumeTemplateSampleDownloadView.as_view(),
        name="resume-template-sample-download",
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
        "projects/generate/",
        ResumeProjectsGenerationView.as_view(),
        name="resume-projects-generate",
    ),

    path(
        "profile/",
        ResumeProfileView.as_view(),
        name="resume-profile",
    ),

    path(
        "wizard/turn/",
        ResumeWizardTurnView.as_view(),
        name="resume-wizard-turn",
    ),

    path(
        "wizard/finalize/",
        ResumeWizardFinalizeView.as_view(),
        name="resume-wizard-finalize",
    ),

    path(
        "enrich/<int:resume_id>/analyze/",
        ResumeEnrichmentAnalyzeView.as_view(),
        name="resume-enrichment-analyze",
    ),

    path(
        "enrich/<int:resume_id>/enhance/",
        ResumeEnrichmentEnhanceView.as_view(),
        name="resume-enrichment-enhance",
    ),

    path(
        "enrich/<int:resume_id>/apply/",
        ResumeEnrichmentApplyView.as_view(),
        name="resume-enrichment-apply",
    ),

    path(
        "enrich/<int:resume_id>/regenerate/",
        ResumeEnrichmentRegenerateView.as_view(),
        name="resume-enrichment-regenerate",
    ),

    path(
        "enrich/<int:resume_id>/apply-regenerated/",
        ResumeEnrichmentApplyRegeneratedView.as_view(),
        name="resume-enrichment-apply-regenerated",
    ),
]