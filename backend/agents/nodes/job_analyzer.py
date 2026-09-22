from agents.schemas import JobRequirements
from agents.services.structured_llm import generate_structured_output


def _normalize_text(value):
    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().split())


def _skill_is_explicitly_supported(
    skill,
    job_description,
):
    skill_text = _normalize_text(skill)
    job_text = _normalize_text(job_description)

    if not skill_text:
        return False

    # Direct match
    if skill_text in job_text:
        return True

    # Explicit terminology aliases
    aliases = {
        "continuous integration": [
            "continuous integration",
            "ci tools",
            "ci/cd",
            "ci cd",
        ],

        "source control": [
            "source control",
            "version control",
        ],

        "microservices": [
            "microservice",
            "microservices",
        ],

        "automated build and deployment pipelines": [
            "automated build and deployment pipelines",
            "automated build and deployment",
            "automated build",
            "automated deployment",
            "build and deployment pipelines",
            "build/deployment pipelines",
            "build and deployment",
        ],

        "javascript": [
            "javascript",
            "java script",
        ],

        "sql": [
            "sql",
        ],

        "asset and wealth management processes": [
            "asset and wealth management processes",
            "asset and wealth management",
            "wealth management processes",
        ],
    }

    for canonical_skill, variants in aliases.items():

        if skill_text != canonical_skill:
            continue

        return any(
            variant in job_text
            for variant in variants
        )

    return False


def _filter_skills_against_job_description(
    skills,
    job_description,
):
    if not isinstance(skills, list):
        return []

    filtered = []

    for skill in skills:

        if not isinstance(skill, str):
            continue

        skill = skill.strip()

        if not skill:
            continue

        if not _skill_is_explicitly_supported(
            skill,
            job_description,
        ):
            continue

        if skill not in filtered:
            filtered.append(skill)

    return filtered


def _add_if_missing(
    skills,
    skill,
):
    """
    Add a canonical skill only if it is not already present.
    """

    if not isinstance(skills, list):
        skills = []

    normalized_skill = _normalize_text(skill)

    for existing_skill in skills:

        if (
            isinstance(existing_skill, str)
            and _normalize_text(existing_skill)
            == normalized_skill
        ):
            return skills

    skills.append(skill)

    return skills


def _recover_explicit_required_skills(
    skills,
    job_description,
):
    """
    Deterministically recover important required skills that
    are explicitly present in the JD but may have been missed
    by the LLM.

    This does NOT infer technologies.
    """

    job_text = _normalize_text(
        job_description
    )

    if not isinstance(skills, list):
        skills = []

    explicit_required_skills = [
        (
            "Python",
            [
                "python",
            ],
        ),
        (
            "Java",
            [
                "java",
            ],
        ),
        (
            "JavaScript",
            [
                "javascript",
                "java script",
            ],
        ),
        (
            "SQL",
            [
                "sql",
            ],
        ),
        (
            "Microservices",
            [
                "microservice",
                "microservices",
            ],
        ),
        (
            "Source control",
            [
                "source control",
                "version control",
            ],
        ),
        (
            "Continuous integration",
            [
                "continuous integration",
                "ci tools",
                "ci/cd",
                "ci cd",
            ],
        ),
        (
            "Automated build and deployment pipelines",
            [
                "automated build and deployment pipelines",
                "automated build and deployment",
                "build and deployment pipelines",
                "build/deployment pipelines",
                "automated build",
                "automated deployment",
            ],
        ),
    ]

    for canonical_skill, variants in explicit_required_skills:

        if any(
            variant in job_text
            for variant in variants
        ):
            skills = _add_if_missing(
                skills,
                canonical_skill,
            )

    return skills


def _recover_explicit_preferred_skills(
    skills,
    job_description,
):
    """
    Deterministically recover preferred/domain skills that
    are explicitly described as desirable or advantageous.

    This does NOT convert every domain mention into a
    preferred skill.
    """

    job_text = _normalize_text(
        job_description
    )

    if not isinstance(skills, list):
        skills = []

    preferred_patterns = [
        (
            "Asset and wealth management processes",
            [
                "asset and wealth management processes",
                "asset and wealth management",
            ],
        ),
    ]

    for canonical_skill, variants in preferred_patterns:

        if not any(
            variant in job_text
            for variant in variants
        ):
            continue

        # Only classify this as preferred if the surrounding
        # JD language indicates desirability/advantage.
        preferred_markers = [
            "preferred",
            "desirable",
            "desirable advantage",
            "advantage",
            "nice to have",
            "bonus",
            "preferred skill",
        ]

        has_preferred_context = any(
            marker in job_text
            for marker in preferred_markers
        )

        if has_preferred_context:
            skills = _add_if_missing(
                skills,
                canonical_skill,
            )

    return skills


def _remove_duplicate_equivalent_skills(
    skills,
):
    """
    Remove obvious equivalent duplicates while preserving
    the canonical wording.
    """

    if not isinstance(skills, list):
        return []

    canonical_aliases = {
        "ci/cd": "continuous integration",
        "ci cd": "continuous integration",
        "version control": "source control",
        "microservice": "microservices",
        "react.js": "ReactJS",
        "react js": "ReactJS",
        "java script": "JavaScript",
    }

    result = []
    seen = set()

    for skill in skills:

        if not isinstance(skill, str):
            continue

        skill = skill.strip()

        if not skill:
            continue

        normalized = _normalize_text(skill)

        canonical = canonical_aliases.get(
            normalized,
            normalized,
        )

        if canonical in seen:
            continue

        seen.add(canonical)

        # Preserve preferred display capitalization
        # for recovered canonical skills.
        if normalized == "ci/cd":
            skill = "Continuous integration"

        elif normalized == "ci cd":
            skill = "Continuous integration"

        elif normalized == "version control":
            skill = "Source control"

        elif normalized == "microservice":
            skill = "Microservices"

        result.append(skill)

    return result


def job_analyzer_node(state):

    job_description = state.get(
        "job_description",
        "",
    ).strip()

    if not job_description:
        raise ValueError(
            "Job description is empty."
        )

    system_prompt = """
You are the Job Analyzer agent in an AI Career Copilot.

Your job is to extract structured requirements from a job description
WITHOUT inventing, expanding, or reclassifying requirements.

==================================================
1. REQUIRED SKILLS
==================================================

required_skills must contain only explicit technical skills, technologies,
programming languages, frameworks, databases, platforms, engineering tools,
or clearly named engineering practices that are presented as requirements.

Examples:

Python
Java
JavaScript
SQL
Microservices
Source control
Continuous integration
Automated build and deployment pipelines

A skill must be explicitly supported by the job description.

Do NOT infer technologies.

For example, if the JD says:

"Automated build and deployment pipelines"

Do NOT add:

Jenkins
GitHub Actions
GitLab CI
Docker
Kubernetes
Azure DevOps

unless explicitly mentioned.

==================================================
2. IMPORTANT: RESPONSIBILITIES ARE NOT SKILLS
==================================================

Keep activities, duties, operational tasks, and job responsibilities inside
the responsibilities field.

Do NOT automatically convert these into required_skills:

- troubleshooting
- root cause analysis
- log monitoring
- metrics analysis
- dashboards
- stakeholder communication
- collaboration
- documentation
- code reviews
- performance troubleshooting
- security handling
- testing activities
- monitoring activities

==================================================
3. TESTING RULE
==================================================

Testing technologies or explicitly named testing tools can be skills.

Examples:

pytest
JUnit
Selenium
Cypress

However, generic testing activities should remain responsibilities.

For example:

"Write unit, integration and regression tests."

Keep this as a responsibility.

Do NOT automatically create:

"Unit tests"
"Integration tests"
"Regression tests"

as required_skills.

==================================================
4. MONITORING RULE
==================================================

Generic monitoring activities remain responsibilities.

For example:

"Monitor application health using logs, metrics and dashboards."

Keep this as a responsibility.

Do NOT create:

"Log monitoring"
"Metrics analysis"
"Dashboards"

as required_skills.

If a specific monitoring technology is explicitly named,
it may be a skill.

==================================================
5. ENGINEERING PRACTICES
==================================================

Some explicitly required engineering practices may be skills.

Examples:

Source control
Continuous integration
CI/CD
Automated build and deployment pipelines

Do not invent specific tools for generic engineering practices.

For example:

"Continuous integration"

does NOT imply:

Jenkins
GitHub Actions
GitLab CI
Azure DevOps

unless explicitly named.

==================================================
6. MICROSERVICES RULE
==================================================

If the JD explicitly requires:

"Microservices"

extract:

"Microservices"

Do not automatically split it into:

Service boundaries
Stateless design
Interservice communication
Resilience patterns

==================================================
7. PREFERRED SKILLS
==================================================

Put a skill in preferred_skills only when the JD explicitly identifies it
as:

- preferred
- desirable
- nice to have
- bonus
- advantageous
- exposure that is explicitly described as desirable

For example:

"Bring exposure to asset and wealth management processes as a desirable
advantage."

Extract:

"Asset and wealth management processes"

as a preferred skill.

Do not move preferred skills into required_skills.

==================================================
8. RESPONSIBILITIES
==================================================

The responsibilities field should contain the actual duties from the JD.

Preserve important responsibilities such as:

- developing applications
- maintaining services
- troubleshooting
- root cause analysis
- monitoring
- code reviews
- documentation
- collaboration
- security
- testing
- performance optimization
- stakeholder interaction

==================================================
9. EXPERIENCE REQUIREMENTS
==================================================

Extract explicit experience requirements.

Do not infer experience requirements.

==================================================
10. EDUCATION REQUIREMENTS
==================================================

Extract education ONLY if the job description explicitly states an
education requirement.

If the JD does NOT mention education, return:

[
    "Not specified"
]

Do NOT infer:

Bachelor's degree
B.Tech
B.E.
Computer Science degree

==================================================
11. NORMALIZATION
==================================================

Normalize only obvious terminology variations.

Examples:

GenAl -> GenAI
Agentic Al -> Agentic AI
Fast API -> FastAPI
React.js -> ReactJS
Large Language Model -> LLMs
Large Language Models -> LLMs
Retrieval Augmented Generation -> RAG
Retrieval-Augmented Generation -> RAG
CI/CD -> CI/CD

Do not convert a broad requirement into a more specific concept.

==================================================
12. NO DUPLICATES
==================================================

Do not duplicate equivalent skills.

For example, do not return both:

"CI/CD"
"Continuous integration"

unless the JD explicitly treats them as separate requirements.

==================================================
13. STRICT OUTPUT FORMAT
==================================================

Return ONLY valid JSON matching the JobRequirements schema.

The output must contain exactly:

{
    "required_skills": [],
    "preferred_skills": [],
    "responsibilities": [],
    "experience_requirements": [],
    "education_requirements": []
}

Every item must be a plain string.

No objects.
No dictionaries.
No nested arrays.
No additional fields.
No markdown.
No explanations.

==================================================
14. FINAL VALIDATION
==================================================

Before returning the result, verify:

1. Every required skill is explicitly supported by the JD.
2. Every preferred skill is explicitly supported by the JD.
3. Responsibilities have not been incorrectly converted into skills.
4. Generic testing activities remain responsibilities.
5. Generic monitoring activities remain responsibilities.
6. Troubleshooting and root-cause activities remain responsibilities.
7. No inferred technologies were added.
8. No invented education requirement exists.
9. Education is "Not specified" when absent from the JD.
10. No duplicate equivalent skills exist.
"""


    user_prompt = f"""
Analyze the following job description.

JOB DESCRIPTION
================

{job_description}


================
IMPORTANT EXTRACTION RULES
================

Extract only what is explicitly present.

For REQUIRED SKILLS, focus on:

- programming languages
- frameworks
- databases
- cloud platforms
- APIs
- named engineering tools
- explicitly required engineering practices
- explicitly required technical technologies

For RESPONSIBILITIES, preserve activities such as:

- development
- maintenance
- troubleshooting
- root cause analysis
- monitoring
- logs
- metrics
- dashboards
- testing activities
- code reviews
- documentation
- collaboration
- security activities
- stakeholder interaction

If the JD explicitly says:

"Automated build and deployment pipelines"

extract:

"Automated build and deployment pipelines"

as a required skill.

If the JD says:

"Bring exposure to asset and wealth management processes as a
desirable advantage"

extract:

"Asset and wealth management processes"

as a preferred skill.

Do NOT add technologies such as:

Jenkins
Docker
GitHub Actions
GitLab CI
Kubernetes

unless the JD explicitly names them.

If the JD says:

"Use Python, Java, JavaScript and SQL to build microservice applications."

Correct required skills:

[
    "Python",
    "Java",
    "JavaScript",
    "SQL",
    "Microservices"
]

If the JD says:

"Experience with source control and continuous integration."

Correct required skills:

[
    "Source control",
    "Continuous integration"
]

If the JD says:

"Experience with Jenkins and Docker."

Correct required skills:

[
    "Jenkins",
    "Docker"
]

Do not add technologies that are not explicitly mentioned.


EDUCATION RULE
===============

If the JD explicitly states an education requirement, extract it.

If the JD does NOT mention education, return:

"Not specified"

Do NOT infer an education requirement.


Return ONLY valid JSON matching the JobRequirements schema.
"""

    result = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=JobRequirements,
    )

    result_data = result.model_dump()

    # ==================================================
    # FILTER LLM OUTPUT
    # ==================================================

    result_data["required_skills"] = (
        _filter_skills_against_job_description(
            result_data.get(
                "required_skills",
                [],
            ),
            job_description,
        )
    )

    result_data["preferred_skills"] = (
        _filter_skills_against_job_description(
            result_data.get(
                "preferred_skills",
                [],
            ),
            job_description,
        )
    )

    # ==================================================
    # RECOVER EXPLICIT REQUIRED SKILLS
    # ==================================================

    result_data["required_skills"] = (
        _recover_explicit_required_skills(
            result_data.get(
                "required_skills",
                [],
            ),
            job_description,
        )
    )

    # ==================================================
    # RECOVER EXPLICIT PREFERRED SKILLS
    # ==================================================

    result_data["preferred_skills"] = (
        _recover_explicit_preferred_skills(
            result_data.get(
                "preferred_skills",
                [],
            ),
            job_description,
        )
    )

    # ==================================================
    # FINAL VALIDATION
    # ==================================================

    result_data["required_skills"] = (
        _filter_skills_against_job_description(
            result_data.get(
                "required_skills",
                [],
            ),
            job_description,
        )
    )

    result_data["preferred_skills"] = (
        _filter_skills_against_job_description(
            result_data.get(
                "preferred_skills",
                [],
            ),
            job_description,
        )
    )

    # Remove equivalent duplicates.
    result_data["required_skills"] = (
        _remove_duplicate_equivalent_skills(
            result_data.get(
                "required_skills",
                [],
            )
        )
    )

    result_data["preferred_skills"] = (
        _remove_duplicate_equivalent_skills(
            result_data.get(
                "preferred_skills",
                [],
            )
        )
    )

    # ==================================================
    # PREVENT REQUIRED/PREFERRED DUPLICATION
    # ==================================================

    required_normalized = {
        _normalize_text(skill)
        for skill in result_data.get(
            "required_skills",
            [],
        )
        if isinstance(skill, str)
    }

    result_data["preferred_skills"] = [
        skill
        for skill in result_data.get(
            "preferred_skills",
            [],
        )
        if (
            _normalize_text(skill)
            not in required_normalized
        )
    ]

    return {
        "job_requirements": result_data
    }