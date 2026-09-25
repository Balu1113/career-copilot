from django.urls import path

from agents.views import ApplicationAgentView

urlpatterns = [
    path(
        "application-agent/",
        ApplicationAgentView.as_view(),
        name="application-agent",
    ),
]