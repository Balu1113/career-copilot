from unittest.mock import patch

from django.test import TestCase

from resume_builder.services.resume_generator import (
    generate_resume_summary,
)


class ResumeSummaryGenerationTests(TestCase):
    @patch("resume_builder.services.resume_generator.generate_structured_output")
    def test_generate_resume_summary_returns_generated_summary(self, mock_generate):
        mock_generate.return_value = {
            "summary": "Product-focused software engineer with 5+ years of experience building scalable web platforms and data-driven applications."
        }

        result = generate_resume_summary(
            {
                "personal": {
                    "name": "Jane Doe",
                    "email": "jane@example.com",
                    "phone": "+1-555-0123",
                    "location": "Seattle, WA",
                },
                "summary": "",
                "skills": {
                    "Programming Languages": ["Python", "JavaScript"],
                    "Frameworks": ["React", "Django"],
                },
                "experience": [
                    {
                        "role": "Software Engineer",
                        "company": "Acme Tech",
                        "bullets": [
                            "Built APIs and dashboards for internal products.",
                            "Improved release reliability and developer velocity.",
                        ],
                    }
                ],
                "projects": [],
            },
            job_description="Build scalable backend systems and modern web experiences.",
        )

        self.assertEqual(
            result,
            "Product-focused software engineer with 5+ years of experience building scalable web platforms and data-driven applications.",
        )
        mock_generate.assert_called_once()
