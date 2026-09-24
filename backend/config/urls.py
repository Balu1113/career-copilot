from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/", include("users.urls")),

    path("api/resumes/", include("resumes.urls")),

    path("api/rag/", include("rag.urls")),

    path(
        "api/jobs/",
        include("jobs.urls"),
    ),

    path(
        "api/career/",
        include("career.urls"),
    ),

    path(
        "api/resume-builder/",
        include("resume_builder.urls"),
    ),


]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)