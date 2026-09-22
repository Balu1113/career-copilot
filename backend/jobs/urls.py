from django.urls import path

from .views import (
    JobAnalysisView,
    JobApplicationListCreateView,
    JobApplicationDetailView,
)

urlpatterns = [
    path(
        "analyze/",
        JobAnalysisView.as_view(),
        name="job-analysis",
    ),

    path(
        "",
        JobApplicationListCreateView.as_view(),
        name="application-list-create",
    ),

    path(
        "<int:pk>/",
        JobApplicationDetailView.as_view(),
        name="application-detail",
    ),
]