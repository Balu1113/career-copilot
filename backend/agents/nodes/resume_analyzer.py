from agents.schemas import ResumeAnalysis
from agents.services.structured_llm import generate_structured_output
from agents.services.skill_matching import (
    build_resume_evidence_text,
    canonicalize,
    has_direct_evidence,
)


def flatten_resume_evidence(resume_intelligence):
    """
    Collect all explicit resume evidence into one normalized set.

    This is used ONLY for deterministic matching validation.
    """

    evidence = set()

    def add_values(values):
        if not values:
            return

        if isinstance(values, str):
            values = [values]

        if isinstance(values, list):
            for value in values:
                if isinstance(value, str):
                    normalized = canonicalize(value)
                    if normalized:
                        evidence.add(normalized)

    add_values(resume_intelligence.get("skills", []))
    add_values(resume_intelligence.get("programming_languages", []))
    add_values(resume_intelligence.get("frameworks", []))
    add_values(resume_intelligence.get("tools_and_technologies", []))
    add_values(resume_intelligence.get("ai_ml_technologies", []))

    # Project evidence
    projects = resume_intelligence.get("projects", [])

    if isinstance(projects, list):
        for project in projects:

            if isinstance(project, dict):
                add_values(project.get("technologies", []))
                add_values(project.get("skills", []))

    # Professional experience evidence
    experience = resume_intelligence.get("experience", [])

    if isinstance(experience, list):
        for entry in experience:

            if not isinstance(entry, dict):
                continue

            add_values(entry.get("technologies", []))
            add_values(entry.get("skills", []))

    return evidence


def extract_job_requirements(job_requirements):
    """
    Extract the authoritative requirement registry from Job Analyzer.

    The registry includes explicit skills from required/preferred lists,
    technical responsibilities, and technology mentions elsewhere in the JD.
    Fall back to the legacy lists for older job-analysis records.
    """

    requirement_items = []
    registry = job_requirements.get("requirement_registry", [])

    if isinstance(registry, list):
        for item in registry:
            if not isinstance(item, dict):
                continue

            display_name = item.get("display_name") or item.get("skill")
            if isinstance(display_name, str) and display_name.strip():
                requirement_items.append((display_name.strip(), item))

    if requirement_items:
        deduplicated = []
        seen = set()

        for requirement, item in requirement_items:
            canonical = (
                (item.get("canonical_group") if isinstance(item, dict) else None)
                or canonicalize(requirement)
                or requirement.lower()
            )

            if canonical in seen:
                continue

            seen.add(canonical)
            deduplicated.append(requirement)

        return deduplicated

    requirements = []
    for key in ["required_skills", "preferred_skills"]:
        values = job_requirements.get(key, [])

        if isinstance(values, str):
            values = [values]

        if isinstance(values, list):
            requirements.extend(value for value in values if isinstance(value, str))

    return requirements


def validate_matching_skills(
    job_requirements,
    resume_intelligence,
):
    job_skills = extract_job_requirements(job_requirements)

    resume_evidence = flatten_resume_evidence(resume_intelligence)
    resume_text = build_resume_evidence_text(resume_intelligence)

    validated = []
    seen = set()

    for job_skill in job_skills:
        if not isinstance(job_skill, str):
            continue

        canonical_skill = canonicalize(job_skill)

        if not canonical_skill or canonical_skill in seen:
            continue

        if has_direct_evidence(
            job_skill,
            resume_evidence,
            resume_text,
        ):
            validated.append(job_skill)
            seen.add(canonical_skill)

    return validated


def resume_analyzer_node(state):

    resume_intelligence = state.get("resume_intelligence", {})
    job_requirements = state.get("job_requirements", {})

    if not resume_intelligence:
        raise ValueError("Resume Intelligence data is empty.")

    if not job_requirements:
        raise ValueError("Job requirements are empty.")

    system_prompt = """
You are a professional AI resume analyzer.

Your task is to compare a candidate's structured resume intelligence
against the requirements extracted from a job description.

The structured resume intelligence is the SOURCE OF TRUTH.

Return ONLY one valid JSON object matching the ResumeAnalysis schema.

==================================================
STRICT MATCHING RULES
==================================================

matching_skills MUST represent:

JOB REQUIREMENTS ∩ EXPLICIT RESUME EVIDENCE

For every job requirement:

1. Check whether it exists in the job requirements.
2. Check whether the same skill is explicitly demonstrated in the
resume.
3. Only then include it in matching_skills.

Do NOT infer skills.

Do NOT assume related technologies are equivalent.

Do NOT infer:

Django → FastAPI
Python → FastAPI
Git → CI/CD
Git → DevOps
Postman → automated testing
WebSockets → Microservices
Django → Microservices
API testing → unit testing
API testing → integration testing
Application maintenance → CI/CD

==================================================
ALLOWED TERMINOLOGY EQUIVALENCE
==================================================

Only use genuine terminology equivalents.

Examples:

React = ReactJS = React.js
GenAI = Generative AI
AI agents and Agentic AI are related concepts, but do not treat them
as exact equivalents unless the resume explicitly demonstrates the
specific terminology.
RAG = Retrieval-Augmented Generation
LLM = Large Language Model
Version control = Source control

Do not extend equivalence beyond the same underlying concept.

==================================================
PROJECT EVIDENCE
==================================================

Project technologies may demonstrate technical skills.

However, project evidence is NOT professional experience.

A project can support matching_skills.

A project must NEVER be inserted into matching_experience.

==================================================
PROFESSIONAL EXPERIENCE
==================================================

matching_experience must contain ONLY entries from the professional
experience section.

Preserve:

company
role
description
technologies

Do not invent information.

==================================================
DEMONSTRATED TOOLS
==================================================

demonstrated_tools should contain technologies explicitly present
in the resume intelligence.

This list can be broader than matching_skills.

==================================================
RELEVANT PROJECTS
==================================================

Return only actual project names from the resume.

Do not invent project names.

==================================================
IMPORTANT
==================================================

Do not put every job requirement into matching_skills.

Do not put every resume skill into matching_skills.

matching_skills is ONLY the intersection.

Return empty arrays where appropriate.

Return ONLY valid JSON.
"""

    user_prompt = f"""
JOB REQUIREMENTS
================

{job_requirements}


CANDIDATE RESUME INTELLIGENCE
=============================

Skills:
{resume_intelligence.get("skills", [])}

Programming Languages:
{resume_intelligence.get("programming_languages", [])}

Frameworks:
{resume_intelligence.get("frameworks", [])}

Tools and Technologies:
{resume_intelligence.get("tools_and_technologies", [])}

AI / ML Technologies:
{resume_intelligence.get("ai_ml_technologies", [])}

Projects:
{resume_intelligence.get("projects", [])}

Professional Experience:
{resume_intelligence.get("experience", [])}


MATCHING REQUIREMENT
====================

For matching_skills:

ONLY include a skill when BOTH conditions are true:

1. It is explicitly listed in the job requirements.
2. It is explicitly demonstrated in the resume intelligence.

Examples:

Job:
Python, Java, JavaScript, SQL, Microservices, Source control

Resume:
Python, JavaScript, SQL, Git

Correct matching_skills:

[
   "Python",
   "JavaScript",
   "SQL",
   "Source control"
]

Incorrect:

[
   "Python",
   "JavaScript",
   "SQL",
   "Microservices",
   "Java"
]

Microservices and Java are not demonstrated.

Git is explicit version control evidence, therefore it can support
Source control.

==================================================
IMPORTANT NON-EQUIVALENCES
==================================================

Git does not prove:

- CI/CD
- Continuous integration tools
- Automated build and deployment pipelines
- DevOps

Postman does not prove:

- Unit tests
- Integration tests
- Regression tests

Django does not prove:

- Microservices

WebSockets do not prove:

- Microservices

Python does not prove:

- Java

Return only explicitly supported matches.
"""

    result = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=ResumeAnalysis,
    )

    result_data = result

    # ==============================================================
    # DETERMINISTIC MATCHING VALIDATION
    # ==============================================================

    result_data["matching_skills"] = validate_matching_skills(
        job_requirements=job_requirements,
        resume_intelligence=resume_intelligence,
    )

    return {"resume_analysis": result_data}
