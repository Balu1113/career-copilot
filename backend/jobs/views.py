from rest_framework import generics, permissions

from .models import JobApplication
from .serializers import JobApplicationSerializer


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


class JobApplicationDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(
            user=self.request.user
        )