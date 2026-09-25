import json
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404

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

from career.models import CareerAnalysis, CareerRoadmap, InterviewSession

from .serializers import (
    CareerAnalysisSerializer,
    CareerAnalysisHistorySerializer,
    InterviewPrepSerializer,
    InterviewAnswerEvaluationSerializer,
)

from .services.interview_analytics import (
    get_interview_performance_analytics,
)
from .services.interview_prep import generate_interview_prep
from .services.resume_optimizer import optimize_resume_for_job
from .services.roadmap_generator import generate_career_roadmap
from .services.interview_simulator import (
    create_interview_session,
    submit_interview_answer,
)


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
                    "evaluation": result,
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


class ResumeOptimizationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        resume_id = request.data.get("resume_id")
        resume_type = request.data.get("resume_type", "uploaded")
        job_description = request.data.get("job_description", "")
        job_requirements = request.data.get("job_requirements", {})

        if not resume_id:
            return Response(
                {"error": "resume_id is required."},
                status=400,
            )

        if not job_description:
            return Response(
                {"error": "job_description is required."},
                status=400,
            )

        if resume_type == "uploaded":
            resume = get_object_or_404(
                Resume,
                id=resume_id,
                user=request.user,
            )

            resume_context = resume.extracted_text

        else:
            generated = get_object_or_404(
                GeneratedResume,
                id=resume_id,
                user=request.user,
            )

            resume_context = generated_resume_to_text(
                generated.content
            )

        if not resume_context or not resume_context.strip():
            return Response(
                {
                    "error": (
                        "Resume content is empty. Please select a resume "
                        "with usable text."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = optimize_resume_for_job(
                resume_context=resume_context,
                job_description=job_description,
                job_requirements=job_requirements,
            )

            return Response(result)

        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=500,
            )


class CareerRoadmapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        analysis_id = request.data.get("analysis_id")
        target_role = request.data.get("target_role") or ""

        if not analysis_id:
            return Response(
                {"detail": "analysis_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(target_role, str):
            return Response(
                {"detail": "target_role must be a string."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_role = target_role.strip()

        try:
            analysis = CareerAnalysis.objects.get(
                id=analysis_id,
                user=request.user,
            )
        except (
            CareerAnalysis.DoesNotExist,
            TypeError,
            ValueError,
        ):
            return Response(
                {"detail": "Career analysis not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            roadmap_data = generate_career_roadmap(
                skill_gap_analysis=analysis.skill_gap_analysis,
                career_recommendation=analysis.career_recommendation,
                resume_intelligence=analysis.resume_intelligence,
                job_description=analysis.job_description,
                target_role=target_role,
            )

            roadmap = CareerRoadmap.objects.create(
                user=request.user,
                career_analysis=analysis,
                title=roadmap_data["title"],
                target_role=(
                    roadmap_data.get("target_role")
                    or target_role
                    or "Target Career Role"
                ),
                roadmap_data=roadmap_data,
            )

            return Response(
                {
                    "id": roadmap.id,
                    "title": roadmap.title,
                    "target_role": roadmap.target_role,
                    "roadmap": roadmap.roadmap_data,
                    "career_analysis_id": analysis.id,
                    "created_at": roadmap.created_at,
                    "updated_at": roadmap.updated_at,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CareerRoadmapListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        roadmaps = CareerRoadmap.objects.filter(
            user=request.user
        ).order_by("-created_at")

        data = []

        for roadmap in roadmaps:
            data.append(
                {
                    "id": roadmap.id,
                    "title": roadmap.title,
                    "target_role": roadmap.target_role,
                    "roadmap": roadmap.roadmap_data,
                    "career_analysis_id": (
                        roadmap.career_analysis_id
                    ),
                    "created_at": roadmap.created_at,
                    "updated_at": roadmap.updated_at,
                }
            )

        return Response(data)


class CareerRoadmapDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, roadmap_id):
        try:
            roadmap = CareerRoadmap.objects.get(
                id=roadmap_id,
                user=request.user,
            )
        except CareerRoadmap.DoesNotExist:
            return Response(
                {"detail": "Career roadmap not found."},
                status=404,
            )

        return Response(
            {
                "id": roadmap.id,
                "title": roadmap.title,
                "target_role": roadmap.target_role,
                "roadmap": roadmap.roadmap_data,
                "career_analysis_id": (
                    roadmap.career_analysis_id
                ),
                "created_at": roadmap.created_at,
                "updated_at": roadmap.updated_at,
            }
        )


class InterviewPerformanceAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            get_interview_performance_analytics(request.user)
        )


class StartInterviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        analysis_id = request.data.get("analysis_id")
        target_role = request.data.get("target_role", "")
        interview_type = request.data.get(
            "interview_type",
            "mixed",
        )

        if not analysis_id:
            return Response(
                {"detail": "analysis_id is required."},
                status=400,
            )

        allowed_types = {
            "mixed",
            "technical",
            "project",
            "gap_based",
            "behavioral",
        }

        if interview_type not in allowed_types:
            return Response(
                {
                    "detail": (
                        "Invalid interview_type. "
                        "Choose mixed, technical, project, "
                        "gap_based, or behavioral."
                    )
                },
                status=400,
            )

        try:
            career_analysis = CareerAnalysis.objects.get(
                id=analysis_id,
                user=request.user,
            )
        except CareerAnalysis.DoesNotExist:
            return Response(
                {"detail": "Career analysis not found."},
                status=404,
            )

        try:
            session = create_interview_session(
                user=request.user,
                career_analysis=career_analysis,
                target_role=target_role,
                interview_type=interview_type,
            )

            questions = session.questions or []

            if not questions:
                return Response(
                    {"detail": "No interview questions available."},
                    status=400,
                )

            current_question = questions[0]

            return Response(
                {
                    "session_id": session.id,
                    "target_role": session.target_role,
                    "interview_type": session.interview_type,
                    "total_questions": len(questions),
                    "current_question_index": 0,
                    "question": current_question,
                    "completed": session.completed,
                },
                status=201,
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )


class SubmitInterviewAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        session_id = request.data.get("session_id")
        answer = request.data.get("answer", "")

        if not session_id:
            return Response(
                {"detail": "session_id is required."},
                status=400,
            )

        if not isinstance(answer, str) or not answer.strip():
            return Response(
                {"detail": "Answer is required."},
                status=400,
            )

        try:
            result = submit_interview_answer(
                user=request.user,
                session_id=session_id,
                answer=answer,
            )

            return Response(
                result,
                status=200,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=500,
            )


class InterviewSessionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(
            InterviewSession,
            id=session_id,
            user=request.user,
        )
        questions = session.questions or []
        current_question = None

        if (
            not session.completed
            and session.current_question_index < len(questions)
        ):
            current_question = questions[
                session.current_question_index
            ]

        return Response(
            {
                "session_id": session.id,
                "career_analysis_id": session.career_analysis_id,
                "target_role": session.target_role,
                "interview_type": session.interview_type,
                "total_questions": len(questions),
                "current_question_index": (
                    session.current_question_index
                ),
                "question": current_question,
                "completed": session.completed,
                "overall_score": session.overall_score,
            }
        )


class InterviewHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = (
            InterviewSession.objects
            .filter(user=request.user)
            .select_related("career_analysis")
            .prefetch_related("responses")
            .order_by("-created_at")
        )

        results = []

        for session in sessions:
            responses = list(
                session.responses.all().order_by("question_index")
            )

            response_data = []

            for response in responses:
                response_data.append(
                    {
                        "id": response.id,
                        "question_index": response.question_index,
                        "question": response.question,
                        "category": response.category,
                        "difficulty": response.difficulty,
                        "answer": response.answer,
                        "score": response.score,
                        "evaluation": response.evaluation,
                        "created_at": response.created_at,
                    }
                )

            scores = [
                response.score
                for response in responses
                if response.score is not None
            ]

            results.append(
                {
                    "id": session.id,
                    "career_analysis_id": (
                        session.career_analysis_id
                    ),
                    "target_role": session.target_role,
                    "interview_type": session.interview_type,
                    "total_questions": len(
                        session.questions or []
                    ),
                    "answered_questions": len(responses),
                    "current_question_index": (
                        session.current_question_index
                    ),
                    "completed": session.completed,
                    "overall_score": session.overall_score,
                    "average_answer_score": (
                        round(sum(scores) / len(scores))
                        if scores
                        else None
                    ),
                    "created_at": session.created_at,
                    "completed_at": session.completed_at,
                    "responses": response_data,
                }
            )

        return Response(results)