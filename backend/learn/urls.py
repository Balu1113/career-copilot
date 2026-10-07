from django.urls import path

from .views import (
    LearnSessionDetailView,
    LearnSessionListCreateView,
    LearnSessionMessageView,
)

urlpatterns = [
    path(
        "sessions/",
        LearnSessionListCreateView.as_view(),
        name="learn-session-list-create",
    ),

    path(
        "sessions/<int:session_id>/",
        LearnSessionDetailView.as_view(),
        name="learn-session-detail",
    ),

    path(
        "sessions/<int:session_id>/messages/",
        LearnSessionMessageView.as_view(),
        name="learn-session-message",
    ),
]
