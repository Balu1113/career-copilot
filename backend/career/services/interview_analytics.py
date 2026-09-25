import re
from collections import defaultdict

from career.models import InterviewSession


WEAK_SCORE_THRESHOLD = 70
GENERIC_SKILL_WORDS = {
    "advanced",
    "architecture",
    "concepts",
    "design",
    "development",
    "fundamentals",
    "knowledge",
    "management",
    "optimization",
    "practices",
    "system",
}


def _average(values):
    if not values:
        return None

    return round(sum(values) / len(values))


def _format_category(value):
    normalized = (value or "general").strip().replace("_", " ")

    if not normalized:
        normalized = "general"

    return " ".join(
        word.capitalize() for word in normalized.split()
    )


def _skill_matches_question(question, skill):
    normalized_question = " ".join(
        (question or "").lower().split()
    )
    normalized_skill = " ".join(skill.lower().split())

    if normalized_skill in normalized_question:
        return True

    words = re.findall(r"[a-z0-9+#.]+", normalized_skill)
    specific_words = [
        word
        for word in words
        if len(word) >= 3 and word not in GENERIC_SKILL_WORDS
    ]

    return any(
        word in normalized_question
        for word in specific_words
    )


def _missing_skills(session):
    if not session.career_analysis:
        return []

    skill_gap_analysis = (
        session.career_analysis.skill_gap_analysis or {}
    )
    missing_skills = skill_gap_analysis.get(
        "missing_skills",
        [],
    )
    skills = []

    for item in missing_skills:
        if isinstance(item, dict):
            skill = str(item.get("skill", "")).strip()
        else:
            skill = str(item or "").strip()

        if skill:
            skills.append(skill)

    return skills


def _build_weak_areas(
    scored_responses,
    performance_by_category,
):
    skill_scores = defaultdict(list)
    skill_names = {}

    for response in scored_responses:
        if response.score >= WEAK_SCORE_THRESHOLD:
            continue

        for skill in _missing_skills(response.session):
            if not _skill_matches_question(
                response.question,
                skill,
            ):
                continue

            key = skill.lower()
            skill_names.setdefault(key, skill)
            skill_scores[key].append(response.score)

    weak_areas = [
        {
            "name": skill_names[key],
            "average_score": _average(scores),
            "questions_answered": len(scores),
            "source": "skill_gap",
        }
        for key, scores in skill_scores.items()
    ]
    weak_areas.sort(
        key=lambda item: (
            item["average_score"],
            -item["questions_answered"],
            item["name"],
        )
    )

    if weak_areas:
        return weak_areas[:5]

    return [
        {
            "name": f"{item['category']} interview questions",
            "average_score": item["average_score"],
            "questions_answered": item["questions_answered"],
            "source": "category",
        }
        for item in performance_by_category
        if item["average_score"] < WEAK_SCORE_THRESHOLD
    ][:5]


def _build_recommended_focus(
    total_sessions,
    completed_sessions,
    in_progress_sessions,
    scored_responses,
    performance_by_category,
    weak_areas,
):
    recommendations = []

    if total_sessions == 0:
        return [
            {
                "title": "Start your first interview",
                "description": (
                    "Complete a resume-grounded interview to begin "
                    "tracking your performance."
                ),
            }
        ]

    if performance_by_category:
        weakest_category = performance_by_category[-1]

        if weakest_category["average_score"] < 85:
            recommendations.append(
                {
                    "title": (
                        "Practice "
                        f"{weakest_category['category'].lower()} "
                        "questions"
                    ),
                    "description": (
                        "Build confidence in your weakest category "
                        f"with a score of "
                        f"{weakest_category['average_score']}/100."
                    ),
                }
            )

    skill_gap_count = sum(
        1
        for item in weak_areas
        if item["source"] == "skill_gap"
    )

    if skill_gap_count:
        recommendations.append(
            {
                "title": "Review identified knowledge gaps",
                "description": (
                    "Focus on the skills connected to your "
                    "lowest-scoring interview answers."
                ),
            }
        )

    low_scoring_count = sum(
        1
        for response in scored_responses
        if response.score < WEAK_SCORE_THRESHOLD
    )

    if low_scoring_count:
        recommendations.append(
            {
                "title": "Reattempt low-scoring questions",
                "description": (
                    f"Practice the {low_scoring_count} question"
                    f"{'s' if low_scoring_count != 1 else ''} "
                    "scoring below 70 and compare your improvement."
                ),
            }
        )

    if not recommendations and completed_sessions:
        recommendations.append(
            {
                "title": "Maintain interview consistency",
                "description": (
                    "Your answers are performing consistently. Continue "
                    "practicing to maintain your score."
                ),
            }
        )

    if not recommendations and in_progress_sessions:
        recommendations.append(
            {
                "title": "Complete your in-progress interview",
                "description": (
                    "Finish the remaining questions to add a completed "
                    "score to your performance trend."
                ),
            }
        )

    if not recommendations and scored_responses:
        recommendations.append(
            {
                "title": "Complete a scored interview",
                "description": (
                    "Finish an interview with evaluated answers to unlock "
                    "your full performance summary."
                ),
            }
        )

    return recommendations[:3]


def get_interview_performance_analytics(user):
    sessions = list(
        InterviewSession.objects.filter(user=user)
        .select_related("career_analysis")
        .prefetch_related("responses")
    )
    completed_sessions = [
        session
        for session in sessions
        if session.completed
    ]
    in_progress_sessions = [
        session
        for session in sessions
        if not session.completed
    ]
    responses = []

    for session in sessions:
        for response in session.responses.all():
            response.session = session
            responses.append(response)
    scored_responses = [
        response
        for response in responses
        if response.score is not None
    ]
    completed_scores = [
        session.overall_score
        for session in completed_sessions
        if session.overall_score is not None
    ]
    response_scores = [
        response.score
        for response in scored_responses
    ]
    category_data = defaultdict(
        lambda: {
            "scores": [],
            "questions_answered": 0,
        }
    )

    for response in responses:
        category = _format_category(response.category)
        category_data[category]["questions_answered"] += 1

        if response.score is not None:
            category_data[category]["scores"].append(
                response.score
            )

    performance_by_category = [
        {
            "category": category,
            "average_score": _average(data["scores"]),
            "questions_answered": data["questions_answered"],
        }
        for category, data in category_data.items()
        if data["scores"]
    ]
    performance_by_category.sort(
        key=lambda item: item["average_score"],
        reverse=True,
    )

    recent_completed = [
        session
        for session in completed_sessions
        if session.overall_score is not None
    ]
    recent_completed.sort(
        key=lambda session: (
            session.completed_at or session.created_at,
            session.id,
        ),
        reverse=True,
    )
    recent_completed = list(reversed(recent_completed[-5:]))
    recent_scores = [
        {
            "session_id": session.id,
            "target_role": session.target_role,
            "score": session.overall_score,
            "completed_at": (
                session.completed_at or session.created_at
            ),
        }
        for session in recent_completed
    ]

    weak_areas = _build_weak_areas(
        scored_responses,
        performance_by_category,
    )
    recommended_focus = _build_recommended_focus(
        total_sessions=len(sessions),
        completed_sessions=len(completed_sessions),
        in_progress_sessions=len(in_progress_sessions),
        scored_responses=scored_responses,
        performance_by_category=performance_by_category,
        weak_areas=weak_areas,
    )
    completion_rate = (
        round((len(completed_sessions) / len(sessions)) * 100, 2)
        if sessions
        else 0
    )

    return {
        "summary": {
            "overall_average": _average(completed_scores),
            "completed_interviews": len(completed_sessions),
            "total_interviews": len(sessions),
            "in_progress_interviews": len(in_progress_sessions),
            "questions_answered": len(responses),
            "average_answer_score": _average(response_scores),
            "completion_rate": completion_rate,
        },
        "performance_by_category": performance_by_category,
        "recent_scores": recent_scores,
        "weak_areas": weak_areas,
        "recommended_focus": recommended_focus,
    }
