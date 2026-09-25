from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from agents.application_agent.service import run_application_agent

class ApplicationAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        job = request.data.get("job")
        resume = request.data.get("resume")

        if not isinstance(job, dict):
            return Response(
                {"detail": "Job data is required."},
                status=400,
            )

        if not isinstance(resume, dict):
            return Response(
                {"detail": "Resume data is required."},
                status=400,
            )

        try:
            result = run_application_agent(
                job=job,
                resume=resume,
            )

            return Response(
                {
                    "status": "awaiting_approval",
                    "approval_required": result.get(
                        "approval_required",
                        True,
                    ),
                    "approved": result.get(
                        "approved",
                        False,
                    ),
                    "application_data": result.get(
                        "application_data",
                        {},
                    ),
                    "optimization": result.get(
                        "optimization",
                        {},
                    ),
                    "job_requirements": result.get(
                        "job_requirements",
                        {},
                    ),
                }
            )

        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )