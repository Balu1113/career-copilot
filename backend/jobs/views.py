from rest_framework import permissions, status,generics
from rest_framework.response import Response
from rest_framework.views import APIView

from resumes.models import Resume
from rag.services.vector_store import load_resume_vector_store

from .serializers import JobAnalysisSerializer
from .services.analyzer import analyze_job_description
from .models import JobApplication
from .serializers import JobApplicationSerializer

class JobAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobAnalysisSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        resume_id = serializer.validated_data[
            "resume_id"
        ]

        job_description = serializer.validated_data[
            "job_description"
        ]

        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )

        except Resume.DoesNotExist:
            return Response(
                {"error": "Resume not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            vector_store = load_resume_vector_store(
                resume.id
            )

            documents = vector_store.similarity_search(
                job_description,
                k=6,
            )

            resume_context = "\n\n".join(
                document.page_content
                for document in documents
            )

            analysis = analyze_job_description(
                resume_context=resume_context,
                job_description=job_description,
            )

            return Response({
                "resume_id": resume.id,
                "analysis": analysis,
            })

        except FileNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError:
            return Response(
                {
                    "error": (
                        "The AI returned an invalid "
                        "analysis format."
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        except Exception as exc:
            return Response(
                {
                    "error": "Job analysis failed.",
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class JobApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class JobApplicationDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        )