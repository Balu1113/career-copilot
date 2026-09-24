"""
Deterministic multi-JD fixtures.

Each scenario pairs a job description from an unrelated technology
stack with a fixed Django/GenAI resume profile so the skill-gap
pipeline can be exercised without any LLM calls.
"""

from agents.services.skill_matching import canonicalize


BASE_RESUME_INTELLIGENCE = {
    "professional_summary": (
        "AI/ML-focused Python developer with hands-on experience in "
        "Generative AI, Agentic AI and Retrieval-Augmented Generation (RAG). "
        "Backend experience building production applications with Python, "
        "Django, Django REST Framework, PostgreSQL, MySQL and Redis."
    ),
    "skills": [
        "Generative AI",
        "Agentic AI",
        "RAG",
        "LangChain",
        "LangGraph",
        "Prompt Engineering",
        "Python",
        "SQL",
        "JavaScript",
        "Django",
        "Django REST Framework",
        "REST APIs",
        "React",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Git",
        "GitHub",
    ],
    "programming_languages": ["Python", "SQL", "JavaScript"],
    "frameworks": ["Django", "Django REST Framework", "React"],
    "tools_and_technologies": [
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Postman",
        "Git",
        "GitHub",
    ],
    "ai_ml_technologies": [
        "Generative AI",
        "RAG",
        "LangChain",
        "Scikit-learn",
        "TensorFlow",
    ],
    "projects": [
        {
            "name": "Digital Employee Platform",
            "description": [
                "AI-integrated employee platform with AI calling agents "
                "and AI-driven workflows."
            ],
            "technologies": ["Python", "Django", "PostgreSQL", "React"],
        }
    ],
    "experience": [
        {
            "company": "Pranathi Software Services Pvt. Ltd.",
            "role": "Junior Python Developer",
            "description": [
                "Develop and maintain backend applications using Python, "
                "Django and Django REST Framework."
            ],
            "technologies": ["Python", "Django", "PostgreSQL"],
        }
    ],
    "education": [],
    "certifications": [],
}


CLOUD_INFRA_JD = {
    "name": "cloud_infra",
    "job_requirements": {
        "required_skills": [
            "Python",
            "Kafka",
            "Kubernetes",
            "AWS",
            "PyTorch",
            "PostgreSQL",
            "CI/CD",
        ],
        "preferred_skills": ["Docker", "Terraform"],
        "responsibilities": [],
        "experience_requirements": [],
        "education_requirements": [],
    },
    "matching_skills": ["Python", "PostgreSQL"],
    "semantic_decisions": {
        canonicalize("CI/CD"): "missing",
        canonicalize("Kafka"): "missing",
        canonicalize("Kubernetes"): "missing",
        canonicalize("AWS"): "missing",
        canonicalize("PyTorch"): "missing",
        canonicalize("Docker"): "missing",
        canonicalize("Terraform"): "missing",
    },
}


ENTERPRISE_JAVA_JD = {
    "name": "enterprise_java",
    "job_requirements": {
        "required_skills": [
            "Java",
            "Spring Boot",
            "Microservices",
            "MongoDB",
            "Kafka",
            "Azure",
        ],
        "preferred_skills": ["Docker", "CI/CD"],
        "responsibilities": [],
        "experience_requirements": [],
        "education_requirements": [],
    },
    "matching_skills": [],
    "semantic_decisions": {
        canonicalize("Java"): "missing",
        canonicalize("Spring Boot"): "partial",  # Django backend experience
        canonicalize("Microservices"): "missing",
        canonicalize("MongoDB"): "missing",
        canonicalize("Kafka"): "missing",
        canonicalize("Azure"): "missing",
        canonicalize("Docker"): "missing",
        canonicalize("CI/CD"): "missing",
    },
}


DATA_ENGINEERING_JD = {
    "name": "data_engineering",
    "job_requirements": {
        "required_skills": [
            "Python",
            "Spark",
            "Airflow",
            "Snowflake",
            "SQL",
            "AWS",
        ],
        "preferred_skills": ["dbt", "Kafka"],
        "responsibilities": [],
        "experience_requirements": [],
        "education_requirements": [],
    },
    "matching_skills": ["Python", "SQL"],
    "semantic_decisions": {
        canonicalize("Spark"): "missing",
        canonicalize("Airflow"): "missing",
        canonicalize("Snowflake"): "missing",
        canonicalize("AWS"): "missing",
        canonicalize("dbt"): "missing",
        canonicalize("Kafka"): "missing",
    },
}


FRONTEND_JD = {
    "name": "frontend",
    "job_requirements": {
        "required_skills": [
            "TypeScript",
            "React",
            "Next.js",
            "GraphQL",
            "Jest",
            "AWS",
        ],
        "preferred_skills": ["Tailwind CSS", "CI/CD"],
        "responsibilities": [],
        "experience_requirements": [],
        "education_requirements": [],
    },
    "matching_skills": ["React"],
    "semantic_decisions": {
        canonicalize("TypeScript"): "missing",
        canonicalize("Next.js"): "missing",
        canonicalize("GraphQL"): "missing",
        canonicalize("Jest"): "missing",
        canonicalize("AWS"): "missing",
        canonicalize("Tailwind CSS"): "missing",
        canonicalize("CI/CD"): "missing",
    },
}


ALL_JD_SCENARIOS = [
    CLOUD_INFRA_JD,
    ENTERPRISE_JAVA_JD,
    DATA_ENGINEERING_JD,
    FRONTEND_JD,
]


def build_state(scenario):
    """Build a skill_gap_node input state from a scenario dict."""

    return {
        "resume_intelligence": BASE_RESUME_INTELLIGENCE,
        "job_requirements": scenario["job_requirements"],
        "resume_analysis": {
            "matching_skills": list(scenario["matching_skills"]),
        },
    }


def unique_canonical_requirements(job_requirements):
    """All unique canonical requirement keys for a JD."""

    keys = set()
    for skill in (
        job_requirements.get("required_skills", [])
        + job_requirements.get("preferred_skills", [])
    ):
        canonical = canonicalize(skill)
        if canonical:
            keys.add(canonical)
    return keys
