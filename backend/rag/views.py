from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from resumes.models import Resume

from .serializers import ResumeQuestionSerializer
from .services.llm import generate_resume_answer
from .services.vector_store import load_resume_vector_store


class ResumeQuestionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ResumeQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_id = serializer.validated_data["resume_id"]
        question = serializer.validated_data["question"]

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
                question,
                k=4,
            )

            context = "\n\n".join(
                document.page_content
                for document in documents
            )

            answer = generate_resume_answer(
                question=question,
                context=context,
            )

            return Response({
                "resume_id": resume.id,
                "question": question,
                "answer": answer,
            })

        except FileNotFoundError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as exc:
            return Response(
                {
                    "error": "Failed to generate answer.",
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )