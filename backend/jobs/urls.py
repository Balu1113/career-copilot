from django.urls import path

from .views import (
    JobApplicationDetailView,
    JobApplicationListCreateView,
    JobSearchView,
    RecommendedJobsView,
    ApplicationAnalyticsView,
    ApproveApplicationView
)


urlpatterns = [
    path(
        "search/",
        JobSearchView.as_view(),
        name="job-search",
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

    path(
        "recommended/",
        RecommendedJobsView.as_view(),
        name="recommended-jobs",
    ),

    path(
        "analytics/",
        ApplicationAnalyticsView.as_view(),
        name="application-analytics",
    ),

    path(
        "approve-application/",
        ApproveApplicationView.as_view(),
        name="approve-application",
    ),
]