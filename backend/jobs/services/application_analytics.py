from datetime import timedelta

from django.utils import timezone

from jobs.models import JobApplication


def get_application_analytics(user):
    applications = JobApplication.objects.filter(user=user)

    total = applications.count()

    status_counts = {
        "saved": applications.filter(status="saved").count(),
        "applied": applications.filter(status="applied").count(),
        "interview": applications.filter(status="interview").count(),
        "offer": applications.filter(status="offer").count(),
        "rejected": applications.filter(status="rejected").count(),
    }

    interview_count = status_counts["interview"]
    offer_count = status_counts["offer"]

    interview_rate = (
        round((interview_count / total) * 100, 2)
        if total
        else 0
    )

    offer_rate = (
        round((offer_count / total) * 100, 2)
        if total
        else 0
    )

    rejection_rate = (
        round((status_counts["rejected"] / total) * 100, 2)
        if total
        else 0
    )

    today = timezone.localdate()

    week_start = today - timedelta(days=today.weekday())

    month_start = today.replace(day=1)

    applications_this_week = applications.filter(
        created_at__date__gte=week_start
    ).count()

    applications_this_month = applications.filter(
        created_at__date__gte=month_start
    ).count()

    follow_ups_due = applications.filter(
        follow_up_date__isnull=False,
        follow_up_date__lte=today,
        status__in=["saved", "applied", "interview"],
    ).count()

    return {
        "total": total,
        **status_counts,
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
        "rejection_rate": rejection_rate,
        "applications_this_week": applications_this_week,
        "applications_this_month": applications_this_month,
        "follow_ups_due": follow_ups_due,
    }