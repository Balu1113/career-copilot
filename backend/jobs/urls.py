from django.urls import path

from .views import (
    JobApplicationListCreateView,
    JobApplicationDetailView,
)


urlpatterns = [
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