from django.urls import path

from .views import ResumeQuestionView


urlpatterns = [
    path(
        "ask/",
        ResumeQuestionView.as_view(),
        name="resume-question",
    ),
]