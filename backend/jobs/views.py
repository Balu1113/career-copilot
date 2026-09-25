from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import JobApplication
from .serializers import JobApplicationSerializer
from .services.job_provider import IndianAPIJobProvider
from .services.job_recommender import JobRecommender
from jobs.services.application_analytics import get_application_analytics

class JobApplicationListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )

class ApplicationAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        analytics = get_application_analytics(request.user)
        return Response(analytics)
    
class JobApplicationDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        )
    

class JobSearchView(APIView):
    """
    Search real Indian job listings through IndianAPI.
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):
        title = request.query_params.get(
            "title",
            "",
        ).strip()

        location = request.query_params.get(
            "location",
            "",
        ).strip()

        company = request.query_params.get(
            "company",
            "",
        ).strip()

        experience = request.query_params.get(
            "experience",
            "",
        ).strip()

        job_type = request.query_params.get(
            "job_type",
            "",
        ).strip()

        limit_param = request.query_params.get(
            "limit",
            "10",
        )

        try:
            limit = int(limit_param)
        except (TypeError, ValueError):
            return Response(
                {
                    "detail": (
                        "limit must be a valid integer."
                    )
                },
                status=400,
            )

        # Keep the external API request bounded.
        limit = max(1, min(limit, 20))

        if not any(
            [
                title,
                location,
                company,
                experience,
                job_type,
            ]
        ):
            return Response(
                {
                    "detail": (
                        "Provide at least one search "
                        "parameter."
                    )
                },
                status=400,
            )

        try:
            provider = IndianAPIJobProvider()

            jobs = provider.search_jobs(
                title=title or None,
                location=location or None,
                company=company or None,
                experience=experience or None,
                job_type=job_type or None,
                limit=limit,
            )

            return Response(
                {
                    "count": len(jobs),
                    "jobs": jobs,
                },
                status=200,
            )

        except RuntimeError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=502,
            )

        except Exception as exc:
            return Response(
                {
                    "detail": (
                        "Unable to search jobs."
                    )
                },
                status=500,
            )
        

class RecommendedJobsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        resume_id = request.query_params.get("resume_id", "").strip()
        resume_type = request.query_params.get(
            "resume_type",
            "uploaded",
        ).strip()

        location = request.query_params.get(
            "location",
            "",
        ).strip()

        limit_param = request.query_params.get(
            "limit",
            "10",
        )

        if not resume_id:
            return Response(
                {"detail": "resume_id is required."},
                status=400,
            )

        try:
            resume_id = int(resume_id)
        except (TypeError, ValueError):
            return Response(
                {"detail": "resume_id must be a valid integer."},
                status=400,
            )

        try:
            limit = int(limit_param)
        except (TypeError, ValueError):
            return Response(
                {"detail": "limit must be a valid integer."},
                status=400,
            )

        limit = max(1, min(limit, 20))

        try:
            if resume_type == "uploaded":
                from resumes.models import Resume

                resume = Resume.objects.get(
                    id=resume_id,
                    user=request.user,
                )

                resume_intelligence = resume.resume_intelligence

            elif resume_type == "generated":
                from resume_builder.models import GeneratedResume

                generated_resume = GeneratedResume.objects.get(
                    id=resume_id,
                    user=request.user,
                )

                resume_intelligence = {
                    "skills": [],
                    "programming_languages": [],
                    "frameworks": [],
                    "tools_and_technologies": [],
                    "ai_ml_technologies": [],
                }

                content = generated_resume.content or {}

                skills = content.get("skills", {})

                if isinstance(skills, dict):
                    for values in skills.values():
                        if isinstance(values, list):
                            resume_intelligence["skills"].extend(
                                value
                                for value in values
                                if isinstance(value, str)
                            )

                projects = content.get("projects", [])

                if isinstance(projects, list):
                    for project in projects:
                        if not isinstance(project, dict):
                            continue

                        technologies = project.get(
                            "technologies",
                            [],
                        )

                        if isinstance(technologies, list):
                            resume_intelligence[
                                "skills"
                            ].extend(
                                value
                                for value in technologies
                                if isinstance(value, str)
                            )

            else:
                return Response(
                    {
                        "detail": (
                            "resume_type must be "
                            "'uploaded' or 'generated'."
                        )
                    },
                    status=400,
                )

        except Resume.DoesNotExist:
            return Response(
                {"detail": "Resume not found."},
                status=404,
            )

        except GeneratedResume.DoesNotExist:
            return Response(
                {"detail": "Generated resume not found."},
                status=404,
            )

        except AttributeError:
            return Response(
                {
                    "detail": (
                        "Resume intelligence is not "
                        "available for this resume."
                    )
                },
                status=400,
            )

        try:
            recommender = JobRecommender()

            jobs = recommender.recommend_jobs(
                resume_intelligence=resume_intelligence,
                location=location or None,
                limit=limit,
            )

            return Response(
                {
                    "count": len(jobs),
                    "jobs": jobs,
                },
                status=200,
            )

        except RuntimeError as exc:
            return Response(
                {"detail": str(exc)},
                status=502,
            )

        except Exception:
            return Response(
                {"detail": "Unable to recommend jobs."},
                status=500,
            )
        

class ApproveApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        company = request.data.get("company", "").strip()
        job_title = request.data.get("job_title", "").strip()

        if not company:
            return Response(
                {"detail": "Company is required."},
                status=400,
            )

        if not job_title:
            return Response(
                {"detail": "Job title is required."},
                status=400,
            )

        application = JobApplication.objects.create(
            user=request.user,
            company=company,
            job_title=job_title,
            job_url=request.data.get("job_url") or None,
            status="applied",
            applied_date=timezone.localdate(),
            follow_up_date=request.data.get("follow_up_date") or None,
            notes=request.data.get("notes", ""),
        )

        serializer = JobApplicationSerializer(application)

        return Response(
            serializer.data,
            status=201,
        )