import os

import requests


class IndianAPIJobProvider:
    """
    Provider for real job listings from IndianAPI.

    The API key is kept on the Django backend and is never exposed
    to the React frontend.
    """

    BASE_URL = "https://jobs.indianapi.in/jobs"

    def __init__(self):
        self.api_key = os.getenv(
            "INDIANAPI_JOBS_API_KEY"
        )

    def _headers(self):
        if not self.api_key:
            raise RuntimeError(
                "INDIANAPI_JOBS_API_KEY is not configured."
            )

        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }

    def search_jobs(
        self,
        title=None,
        location=None,
        company=None,
        experience=None,
        job_type=None,
        limit=10,
    ):
        """
        Search real job listings.

        All filtering is performed through the external Jobs API.
        """

        params = {
            "limit": str(limit),
        }

        if title:
            params["title"] = title.strip()

        if location:
            params["location"] = location.strip()

        if company:
            params["company"] = company.strip()

        if experience:
            params["experience"] = experience.strip()

        if job_type:
            params["job_type"] = job_type.strip()

        try:
            response = requests.get(
                self.BASE_URL,
                headers=self._headers(),
                params=params,
                timeout=15,
            )

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Unable to connect to IndianAPI: {exc}"
            ) from exc

        if response.status_code == 401:
            raise RuntimeError(
                "IndianAPI rejected the API key."
            )

        if response.status_code == 422:
            try:
                details = response.json()
            except ValueError:
                details = response.text

            raise RuntimeError(
                f"IndianAPI rejected the search parameters: {details}"
            )

        if response.status_code >= 500:
            raise RuntimeError(
                "IndianAPI is currently unavailable. "
                "Please try again later."
            )

        if not response.ok:
            try:
                details = response.json()
            except ValueError:
                details = response.text

            raise RuntimeError(
                f"IndianAPI request failed "
                f"with status {response.status_code}: {details}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "IndianAPI returned an invalid JSON response."
            ) from exc

        return self._normalize_jobs(data)

    @staticmethod
    def _normalize_jobs(data):
        """
        Convert provider-specific job objects into the format
        our Career Copilot uses internally.
        """

        if isinstance(data, dict):
            jobs = data.get("jobs", [])

            if not isinstance(jobs, list):
                jobs = []

        elif isinstance(data, list):
            jobs = data

        else:
            jobs = []

        normalized_jobs = []

        for job in jobs:
            if not isinstance(job, dict):
                continue

            normalized_jobs.append(
                {
                    "id": job.get("id"),
                    "title": (
                        job.get("job_title")
                        or job.get("title")
                        or ""
                    ),
                    "company": (
                        job.get("company")
                        or ""
                    ),
                    "location": (
                        job.get("location")
                        or ""
                    ),
                    "job_type": (
                        job.get("job_type")
                        or ""
                    ),
                    "experience": (
                        job.get("experience")
                        or ""
                    ),
                    "description": (
                        job.get("job_description")
                        or ""
                    ),
                    "responsibilities": (
                        job.get("role_and_responsibility")
                        or ""
                    ),
                    "skills": (
                        job.get("education_and_skills")
                        or ""
                    ),
                    "about_company": (
                        job.get("about_company")
                        or ""
                    ),
                    "apply_link": (
                        job.get("apply_link")
                        or ""
                    ),
                    "posted_date": (
                        job.get("posted_date")
                        or ""
                    ),
                    "source": "IndianAPI",
                }
            )

        return normalized_jobs