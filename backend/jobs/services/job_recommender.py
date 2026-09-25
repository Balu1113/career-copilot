from collections import OrderedDict
from django.core.cache import cache

from jobs.services.job_provider import IndianAPIJobProvider
from agents.services.skill_matching import canonicalize
from agents.services.skill_normalizer import skill_matches


class JobRecommender:
    """
    Finds real Indian jobs from IndianAPI and ranks them
    against the user's demonstrated resume skills.
    """

    def __init__(self):
        self.provider = IndianAPIJobProvider()

    def recommend_jobs(
        self,
        resume_intelligence,
        location=None,
        limit=10,
    ):
        resume_skills = self._extract_resume_skills(
            resume_intelligence
        )

        if not resume_skills:
            return []

        jobs = self._collect_jobs(
            location=location,
        )

        recommended = []

        for job in jobs:
            job_text = self._build_job_text(job)

            if not job_text.strip():
                continue

            matched_skills = []
            missing_skills = []

            for skill in resume_skills:
                if skill_matches(skill, job_text):
                    matched_skills.append(skill)

            job_required_skills = self._extract_job_skills(
                job
            )

            for skill in job_required_skills:
                if not any(
                    canonicalize(skill)
                    == canonicalize(matched)
                    for matched in matched_skills
                ):
                    missing_skills.append(skill)

            score = self._calculate_match_percentage(
                matched_skills,
                job_required_skills,
            )

            recommended.append(
                {
                    **job,
                    "match": {
                        "matched_skills": matched_skills,
                        "missing_skills": missing_skills,
                        "match_percentage": score,
                    },
                }
            )

        recommended.sort(
            key=lambda item: (
                item["match"]["match_percentage"],
                len(item["match"]["matched_skills"]),
            ),
            reverse=True,
        )

        return recommended[:limit]

    def _collect_jobs(self, location=None):
        """
        Fetch jobs from IndianAPI with server-side caching.

        Cached results prevent repeated page refreshes from
        consuming IndianAPI quota.
        """

        normalized_location = (
            (location or "India").strip().lower()
        )

        cache_key = (
            f"recommended_jobs:"
            f"{normalized_location}"
        )

        cached_jobs = cache.get(cache_key)

        if cached_jobs is not None:
            return cached_jobs

        jobs = self.provider.search_jobs(
            title="Python Developer",
            location=location,
            limit=20,
        )

        unique_jobs = OrderedDict()

        for job in jobs:
            key = (
                job.get("apply_link")
                or job.get("id")
                or (
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                )
            )

            if key not in unique_jobs:
                unique_jobs[key] = job

        jobs = list(unique_jobs.values())

        # Cache provider results for 6 hours.
        cache.set(
            cache_key,
            jobs,
            timeout=60 * 60 * 6,
        )

        return jobs

    @staticmethod
    def _extract_resume_skills(resume_intelligence):
        skills = []

        fields = [
            "skills",
            "programming_languages",
            "frameworks",
            "tools_and_technologies",
            "ai_ml_technologies",
        ]

        for field in fields:
            values = resume_intelligence.get(field, [])

            if isinstance(values, list):
                skills.extend(
                    value
                    for value in values
                    if isinstance(value, str)
                )

        unique = OrderedDict()

        for skill in skills:
            key = canonicalize(skill)

            if key and key not in unique:
                unique[key] = skill

        return list(unique.values())

    @staticmethod
    def _extract_job_skills(job):
        """
        Extract skills only from the provider's explicit
        education/skills field.

        We do not ask the LLM to invent requirements here.
        """

        raw_skills = job.get("skills", "")

        if isinstance(raw_skills, list):
            values = raw_skills
        elif isinstance(raw_skills, str):
            values = [
                item.strip()
                for item in raw_skills.replace(
                    "\n",
                    ",",
                ).split(",")
                if item.strip()
            ]
        else:
            values = []

        unique = OrderedDict()

        for skill in values:
            key = canonicalize(skill)

            if key and key not in unique:
                unique[key] = skill

        return list(unique.values())

    @staticmethod
    def _build_job_text(job):
        fields = [
            job.get("title", ""),
            job.get("description", ""),
            job.get("responsibilities", ""),
            job.get("skills", ""),
            job.get("experience", ""),
        ]

        return "\n".join(
            str(value)
            for value in fields
            if value
        )

    @staticmethod
    def _calculate_match_percentage(
        matched_skills,
        required_skills,
    ):
        if not required_skills:
            return 0

        matched = {
            canonicalize(skill)
            for skill in matched_skills
        }

        required = {
            canonicalize(skill)
            for skill in required_skills
        }

        required.discard("")

        if not required:
            return 0

        percentage = (
            len(matched & required)
            / len(required)
        ) * 100

        return round(percentage)