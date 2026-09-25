import json

from django.http import StreamingHttpResponse

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from resumes.models import Resume, ResumeIntelligence
from resumes.serializers import ResumeIntelligenceSerializer
from resumes.services.resume_intelligence import (
    generate_resume_intelligence,
)

from resume_builder.models import GeneratedResume
from resume_builder.services.resume_text import (
    generated_resume_to_intelligence,
    generated_resume_to_text,
)

from rag.services.vector_store import load_resume_vector_store

from agents.services.agent_stream import stream_career_analysis
from agents.services.interview_evaluator import evaluate_interview_answer

from .models import CareerAnalysis

from .serializers import (
    CareerAnalysisSerializer,
    CareerAnalysisHistorySerializer,
    InterviewPrepSerializer,
    InterviewAnswerEvaluationSerializer,
)

from .services.interview_prep import generate_interview_prep


class InterviewPrepView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InterviewPrepSerializer(
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
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as exc:
            return Response(
                {
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CareerAnalysisStreamView(APIView):
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

        resume_type = serializer.validated_data.get(
            "resume_type",
            "uploaded",
        )

        job_description = serializer.validated_data[
            "job_description"
        ]

        if resume_type == "generated":
            try:
                generated = GeneratedResume.objects.get(
                    id=resume_id,
                    user=request.user,
                )

            except GeneratedResume.DoesNotExist:
                return Response(
                    {
                        "error": "Generated resume not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            resume_context = generated_resume_to_text(
                generated.content
            )

            if not resume_context:
                return Response(
                    {
                        "error": (
                            "Generated resume has no "
                            "usable content. Please edit it "
                            "before running career analysis."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                resume_intelligence = (
                    generate_resume_intelligence(
                        resume_context
                    )
                )
            except Exception:
                resume_intelligence = (
                    generated_resume_to_intelligence(
                        generated.content
                    )
                )

            resume = generated.source_resume
            resume_title = generated.title

        else:
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

            resume_intelligence = ResumeIntelligenceSerializer(
                resume.intelligence
            ).data

            resume_context = resume.extracted_text
            resume_title = resume.title

        if not resume_context or not resume_context.strip():
            return Response(
                {
                    "error": (
                        "Resume text could not be extracted. "
                        "Please upload the resume again."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        def event_stream():
            try:
                yield (
                    "data: "
                    + json.dumps(
                        {
                            "type": "started"
                        }
                    )
                    + "\n\n"
                )

                final_result = {}

                for event in stream_career_analysis(
                    resume_context,
                    job_description,
                    resume_intelligence=resume_intelligence,
                ):
                    yield (
                        "data: "
                        + json.dumps(event)
                        + "\n\n"
                    )

                    if event["type"] == "node_completed":

                        node = event["node"]

                        data = event.get(
                            "data",
                            {}
                        )

                        if node == "resume_intelligence":

                            final_result[
                                "resume_intelligence"
                            ] = data.get(
                                "resume_intelligence",
                                {}
                            )

                        elif node == "job_analyzer":

                            final_result[
                                "job_requirements"
                            ] = data.get(
                                "job_requirements",
                                {}
                            )

                        elif node == "resume_analyzer":

                            final_result[
                                "resume_analysis"
                            ] = data.get(
                                "resume_analysis",
                                {}
                            )

                        elif node == "skill_gap":

                            final_result[
                                "skill_gap_analysis"
                            ] = data.get(
                                "skill_gap_analysis",
                                {}
                            )

                        elif node == "career_advisor":

                            final_result[
                                "career_recommendation"
                            ] = data.get(
                                "career_recommendation",
                                {}
                            )

                        elif node == "interview_prep":

                            final_result[
                                "interview_preparation"
                            ] = data.get(
                                "interview_preparation",
                                {}
                            )

                    if event["type"] == "workflow_error":
                        return

                required_sections = [
                    "resume_intelligence",
                    "job_requirements",
                    "resume_analysis",
                    "skill_gap_analysis",
                    "career_recommendation",
                    "interview_preparation",
                ]

                if not all(
                    section in final_result
                    for section in required_sections
                ):
                    yield (
                        "data: "
                        + json.dumps(
                            {
                                "type": "workflow_error",
                                "message": (
                                    "Career analysis completed without "
                                    "all required sections."
                                ),
                            }
                        )
                        + "\n\n"
                    )

                    return

                analysis = CareerAnalysis.objects.create(
                    user=request.user,
                    resume=resume,
                    resume_title=resume_title,
                    resume_context=resume_context,
                    job_description=job_description,
                    resume_intelligence=final_result[
                        "resume_intelligence"
                    ],
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
                            "type": "completed",
                            "analysis_id": analysis.id,
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
        ).select_related("resume").order_by("-created_at")

        serializer = CareerAnalysisHistorySerializer(
            analyses,
            many=True,
        )

        return Response(
            serializer.data
        )


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
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CareerAnalysisHistorySerializer(
            analysis
        )

        return Response(
            serializer.data
        )

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
                status=status.HTTP_404_NOT_FOUND,
            )

        analysis.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class CareerDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        analyses = CareerAnalysis.objects.filter(
            user=request.user
        ).select_related("resume").order_by("-created_at")

        total_analyses = analyses.count()

        recent_analyses = analyses[:5]

        recent_data = []

        for analysis in recent_analyses:

            job_requirements = (
                analysis.job_requirements or {}
            )

            resume_analysis = (
                analysis.resume_analysis or {}
            )

            skill_gap = (
                analysis.skill_gap_analysis or {}
            )

            required_skills = job_requirements.get(
                "required_skills",
                []
            )

            preferred_skills = job_requirements.get(
                "preferred_skills",
                []
            )

            matching_skills = resume_analysis.get(
                "matching_skills",
                []
            )

            missing_skills = skill_gap.get(
                "missing_skills",
                []
            )

            recent_data.append(
                {
                    "id": analysis.id,

                    "resume_id": analysis.resume_id,

                    "resume_title": (
                        analysis.resume_title
                        or (
                            analysis.resume.title
                            if analysis.resume
                            else None
                        )
                    ),

                    "job_description":
                        analysis.job_description,

                    "required_skills_count":
                        len(required_skills),

                    "preferred_skills_count":
                        len(preferred_skills),

                    "matching_skills_count":
                        len(matching_skills),

                    "missing_skills_count":
                        len(missing_skills),

                    "created_at":
                        analysis.created_at,
                }
            )

        return Response(
            {
                "total_analyses": total_analyses,
                "recent_analyses": recent_data,
            }
        )


class InterviewAnswerEvaluationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InterviewAnswerEvaluationSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        analysis_id = serializer.validated_data[
            "analysis_id"
        ]

        question = serializer.validated_data[
            "question"
        ]

        category = serializer.validated_data[
            "category"
        ]

        difficulty = serializer.validated_data[
            "difficulty"
        ]

        answer = serializer.validated_data[
            "answer"
        ]

        try:
            analysis = CareerAnalysis.objects.get(
                id=analysis_id,
                user=request.user,
            )

        except CareerAnalysis.DoesNotExist:
            return Response(
                {
                    "error": "Career analysis not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            resume_context = (
                analysis.resume_context
                or (
                    analysis.resume.extracted_text
                    if analysis.resume
                    else ""
                )
                or ""
            )

            job_requirements = (
                analysis.job_requirements
                or {}
            )

            result = evaluate_interview_answer(
                question=question,
                category=category,
                difficulty=difficulty,
                user_answer=answer,
                resume_context=resume_context,
                job_requirements=job_requirements,
            )

            return Response(
                {
                    "analysis_id": analysis.id,
                    "question": question,
                    "category": category,
                    "difficulty": difficulty,
                    "evaluation": result.model_dump(),
                }
            )

        except Exception as exc:
            return Response(
                {
                    "error": (
                        "Interview answer evaluation failed."
                    ),
                    "details": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )