from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from resumes.models import Resume, ResumeIntelligence
from rag.services.vector_store import load_resume_vector_store

from agents.graph import build_career_graph

from .serializers import CareerAnalysisSerializer
from resumes.serializers import ResumeIntelligenceSerializer
from .serializers import InterviewPrepSerializer
from .services.interview_prep import generate_interview_prep
from agents.services.agent_stream import stream_career_analysis

import json

from django.http import StreamingHttpResponse

from .models import CareerAnalysis

from .serializers import CareerAnalysisHistorySerializer


class CareerAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CareerAnalysisSerializer(
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
                {
                    "error": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            resume.intelligence
        except ResumeIntelligence.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Resume intelligence has not been generated yet. "
                        "Please generate it before running career analysis."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
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

            resume_intelligence = ResumeIntelligenceSerializer(
                resume.intelligence
            ).data

            initial_state = {
                "job_description": job_description,
                "resume_context": resume_context,
                "resume_intelligence": resume_intelligence,
            }

            graph = build_career_graph()

            result = graph.invoke(
                initial_state
            )

            return Response({
            "resume_id": resume.id,

            "resume_intelligence": result.get(
                "resume_intelligence",
                {}
            ),

            "job_requirements": result.get(
                "job_requirements",
                {}
            ),

                "resume_analysis": result.get(
                    "resume_analysis",
                    {}
                ),

                "skill_gap_analysis": result.get(
                    "skill_gap_analysis",
                    {}
                ),

                "career_recommendation": result.get(
                    "career_recommendation",
                    {}
                ),

                "interview_preparation": result.get(
                    "interview_preparation",
                    {}
                ),
            })

        except FileNotFoundError as exc:
            return Response(
                {
                    "error": str(exc)
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as exc:
            return Response(
                {
                    "error": "Career analysis failed.",
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InterviewPrepView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InterviewPrepSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        resume_id = serializer.validated_data["resume_id"]
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
                status=404,
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

            result = generate_interview_prep(
                resume_context=resume_context,
                job_description=job_description,
            )

            return Response(
                {
                    "resume_id": resume.id,
                    "interview_preparation": result,
                }
            )

        except FileNotFoundError:
            return Response(
                {
                    "error": (
                        "Resume vector store not found. "
                        "Please upload the resume again."
                    )
                },
                status=404,
            )

        except Exception as exc:
            return Response(
                {
                    "error": str(exc),
                },
                status=500,
            )
        
class CareerAnalysisStreamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CareerAnalysisSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        resume_id = serializer.validated_data["resume_id"]
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
                status=404,
            )

        try:
            resume.intelligence
        except ResumeIntelligence.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Resume intelligence has not been generated yet. "
                        "Please generate it before running career analysis."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume_intelligence = ResumeIntelligenceSerializer(
            resume.intelligence
        ).data

        resume_context = resume.extracted_text

        if not resume_context or not resume_context.strip():
            return Response(
                {
                    "error": (
                        "Resume text could not be extracted. "
                        "Please upload the resume again."
                    )
                },
                status=400,
            )

        def event_stream():
            try:
                yield (
                    "data: "
                    + json.dumps(
                        {"type": "started"}
                    )
                    + "\n\n"
                )

                final_result = {}

                for event in stream_career_analysis(
                    resume_context,
                    job_description,
                    resume_intelligence=resume_intelligence,
                ):
                    # Send event to frontend
                    yield (
                        "data: "
                        + json.dumps(event)
                        + "\n\n"
                    )

                    # ----------------------------------
                    # Capture completed agent results
                    # ----------------------------------
                    if event["type"] == "node_completed":
                        node = event["node"]
                        data = event.get("data", {})

                        if node == "resume_intelligence":
                            final_result["resume_intelligence"] = data.get(
                                "resume_intelligence",
                                {}
                            )

                        elif node == "job_analyzer":
                            final_result["job_requirements"] = data.get(
                                "job_requirements",
                                {}
                            )

                        elif node == "resume_analyzer":
                            final_result["resume_analysis"] = data.get(
                                "resume_analysis",
                                {}
                            )

                        elif node == "skill_gap":
                            final_result["skill_gap_analysis"] = data.get(
                                "skill_gap_analysis",
                                {}
                            )

                        elif node == "career_advisor":
                            final_result["career_recommendation"] = data.get(
                                "career_recommendation",
                                {}
                            )

                        elif node == "interview_prep":
                            final_result["interview_preparation"] = data.get(
                                "interview_preparation",
                                {}
                            )

                    # ----------------------------------
                    # Stop if workflow failed
                    # ----------------------------------
                    if event["type"] == "workflow_error":
                        return

                # --------------------------------------
                # Save only successfully completed
                # analyses
                # --------------------------------------
                required_sections = [
                    "resume_intelligence",
                    "job_requirements",
                    "resume_analysis",
                    "skill_gap_analysis",
                    "career_recommendation",
                    "interview_preparation",
                ]

                if all(
                    section in final_result
                    for section in required_sections
                ):
        
                    CareerAnalysis.objects.create(
                        user=request.user,
                        resume=resume,
                        job_description=job_description,
                        resume_intelligence=final_result["resume_intelligence"],
                        job_requirements=final_result[
                            "job_requirements"
                        ],
                        resume_analysis=final_result[
                            "resume_analysis"
                        ],
                        skill_gap_analysis=final_result[
                            "skill_gap_analysis"
                        ],
                        career_recommendation=final_result[
                            "career_recommendation"
                        ],
                        interview_preparation=final_result[
                            "interview_preparation"
                        ],
                    )

                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "completed"
                        }
                    )
                    + "\n\n"
                )

            except Exception as exc:
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "error",
                            "message": str(exc),
                        }
                    )
                    + "\n\n"
                )

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )

        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"

        return response


class CareerAnalysisHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        analyses = CareerAnalysis.objects.filter(
            user=request.user
        )

        serializer = CareerAnalysisHistorySerializer(
            analyses,
            many=True,
        )

        return Response(serializer.data)

class CareerAnalysisHistoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            analysis = CareerAnalysis.objects.get(
                id=pk,
                user=request.user,
            )
        except CareerAnalysis.DoesNotExist:
            return Response(
                {
                    "error": "Career analysis not found."
                },
                status=404,
            )

        serializer = CareerAnalysisHistorySerializer(
            analysis
        )

        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            analysis = CareerAnalysis.objects.get(
                id=pk,
                user=request.user,
            )
        except CareerAnalysis.DoesNotExist:
            return Response(
                {
                    "error": "Career analysis not found."
                },
                status=404,
            )

        analysis.delete()

        return Response(
            {
                "message": "Career analysis deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT,
        )