import re

from agents.schemas import CareerRecommendation
from agents.services.structured_llm import generate_structured_output
from agents.services.skill_normalizer import (
    skill_matches,
)
from agents.services.skill_matching import canonicalize


def _normalize(value):
    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().strip().split())


def _extract_skill_items(items):
    """
    Extract skill names from either:
    - ["Python", "FastAPI"]
    - [{"skill": "Python"}, {"skill": "FastAPI"}]
    """
    skills = []
    seen = set()

    if not isinstance(items, list):
        return skills

    for item in items:
        if isinstance(item, str):
            skill = item.strip()

        elif isinstance(item, dict):
            skill = item.get("skill", "")
            if not isinstance(skill, str):
                continue
            skill = skill.strip()

        else:
            continue

        if not skill:
            continue

        canonical = canonicalize(skill)
        if canonical and canonical in seen:
            continue

        if canonical:
            seen.add(canonical)
        skills.append(skill)

    return skills


def _extract_gap_items(skill_gap_analysis):
    """
    Build one authoritative list containing both missing
    and partial skills.

    Partial skills are included because they still require
    preparation.
    """
    gaps = []
    seen = set()

    missing = _extract_skill_items(
        skill_gap_analysis.get("missing_skills", [])
    )

    partial = _extract_skill_items(
        skill_gap_analysis.get("partial_skills", [])
    )

    for skill in missing + partial:
        canonical = canonicalize(skill)
        if canonical and canonical in seen:
            continue

        if canonical:
            seen.add(canonical)
        gaps.append(skill)

    return gaps



def _extract_structured_skills(resume_intelligence):
    """
    Extract skills from structured fields only.
    This forms the evidence vocabulary for validation.
    """
    skills = set()

    fields = [
        "skills",
        "programming_languages",
        "frameworks",
        "tools_and_technologies",
        "databases",
        "ai_ml_technologies",
    ]

    for field in fields:
        value = resume_intelligence.get(field, [])

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    item = item.strip()
                    if item:
                        skills.add(item)

    return list(skills)


def _build_allowed_terms(
    job_requirements,
    resume_intelligence,
    gap_skills,
):
    """
    Build the vocabulary that the recommendation validator
    is allowed to recognize.

    Sources:
    - Job requirements (required/preferred skills)
    - Resume structured skill fields
    - Authoritative skill gaps

    This prevents the LLM from introducing unrelated
    technologies by only including structured skill data.
    """
    allowed_terms = []

    # Job requirements: required/preferred skills and the authoritative
    # requirement registry.
    if isinstance(job_requirements, dict):
        for field in ["required_skills", "preferred_skills"]:
            skills = job_requirements.get(field, [])
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, str):
                        skill = skill.strip()
                        if skill:
                            allowed_terms.append(skill)

        registry = job_requirements.get("requirement_registry", [])
        if isinstance(registry, list):
            for item in registry:
                if not isinstance(item, dict):
                    continue

                display_name = item.get("display_name") or item.get("skill")
                if isinstance(display_name, str) and display_name.strip():
                    allowed_terms.append(display_name.strip())

    # Resume structured skills only
    allowed_terms.extend(
        _extract_structured_skills(resume_intelligence)
    )

    # Authoritative skill gaps
    allowed_terms.extend(gap_skills)

    normalized = {}

    for term in allowed_terms:
        if not isinstance(term, str):
            continue

        term = term.strip()

        if not term:
            continue

        normalized_term = _normalize(term)

        if normalized_term:
            normalized[normalized_term] = term

    return normalized




def _resume_contains_architecture_evidence(value):
    if isinstance(value, str):
        normalized = _normalize(value)
        return "monolithic" in normalized

    if isinstance(value, list):
        return any(
            _resume_contains_architecture_evidence(item)
            for item in value
        )

    if isinstance(value, dict):
        return any(
            _resume_contains_architecture_evidence(item)
            for item in value.values()
        )

    return False


def _sanitize_architecture_claims(value):
    if isinstance(value, str):
        if "candidate" not in _normalize(value):
            return value

        replacements = [
            (
                r"\bmonolithic(?:-style)?\s+Django applications\b",
                "Django/Django REST Framework backend applications",
            ),
            (
                r"\bmonolithic(?:-style)?\s+backend applications\b",
                "backend applications",
            ),
            (
                r"\bmonolithic(?:-style)?\s+backend\b",
                "backend",
            ),
        ]

        for pattern, replacement in replacements:
            value = re.sub(
                pattern,
                replacement,
                value,
                flags=re.IGNORECASE,
            )

        return value

    if isinstance(value, list):
        return [
            _sanitize_architecture_claims(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: _sanitize_architecture_claims(item)
            for key, item in value.items()
        }

    return value


def _has_extracted_requirements(
    job_requirements,
    missing_skills=None,
    partial_skills=None,
):
    """Return True if job requirements were extracted from the JD."""
    if missing_skills or partial_skills:
        return True

    if isinstance(job_requirements, dict):
        registry = job_requirements.get("requirement_registry", [])
        if isinstance(registry, list) and len(registry) > 0:
            return True

        req_skills = job_requirements.get("required_skills", [])
        if isinstance(req_skills, list) and len(req_skills) > 0:
            return True

        pref_skills = job_requirements.get("preferred_skills", [])
        if isinstance(pref_skills, list) and len(pref_skills) > 0:
            return True

    return False


def _build_match_summary(
    resume_intelligence,
    skill_gap_analysis,
    job_requirements,
    resume_analysis,
):
    """
    Build a factual match summary that is JD-aware.

    Uses resume_analysis.matching_skills as the foundation,
    then appends skill gaps for preparation areas.

    This function must NOT independently classify skills.
    It must use the authoritative classifications from:
    - resume_analysis.matching_skills (demonstrated)
    - skill_gap_analysis.missing_skills (missing)
    - skill_gap_analysis.partial_skills (partial)
    """
    # Get matching skills from resume analysis (JD-specific and authoritative)
    matching_skills = []

    if isinstance(resume_analysis, dict):
        raw_matching = resume_analysis.get("matching_skills", [])
        if isinstance(raw_matching, list):
            matching_skills = [
                skill for skill in raw_matching
                if isinstance(skill, str) and skill.strip()
            ]

    # Separate partial vs missing for different wording
    partial_skills = []
    missing_skills = []

    if isinstance(skill_gap_analysis, dict):
        raw_partial = skill_gap_analysis.get("partial_skills", [])
        if isinstance(raw_partial, list):
            for item in raw_partial:
                if isinstance(item, dict):
                    skill = item.get("skill", "")
                    if isinstance(skill, str) and skill.strip():
                        partial_skills.append(skill.strip())
                elif isinstance(item, str) and item.strip():
                    partial_skills.append(item.strip())

        raw_missing = skill_gap_analysis.get("missing_skills", [])
        if isinstance(raw_missing, list):
            for item in raw_missing:
                if isinstance(item, dict):
                    skill = item.get("skill", "")
                    if isinstance(skill, str) and skill.strip():
                        missing_skills.append(skill.strip())
                elif isinstance(item, str) and item.strip():
                    missing_skills.append(item.strip())

    has_reqs = _has_extracted_requirements(
        job_requirements,
        missing_skills,
        partial_skills,
    )

    # Build first sentence (demonstrated status)
    if matching_skills:
        demonstrated_text = ", ".join(matching_skills[:10])
        first_sentence = f"The candidate demonstrates experience in {demonstrated_text}."
    elif has_reqs:
        first_sentence = "The resume does not explicitly demonstrate any of the listed job requirements."
    else:
        first_sentence = "No specific technologies were extracted from the job description."

    # Build gap sentence with distinction
    if missing_skills and partial_skills:
        missing_text = ", ".join(missing_skills)
        partial_text = ", ".join(partial_skills)
        gap_sentence = (
            f"Key preparation areas include {missing_text} (missing). "
            f"Skills needing additional depth include {partial_text} (partial)."
        )
    elif missing_skills:
        gaps_text = ", ".join(missing_skills)
        gap_sentence = f"Key preparation areas include {gaps_text}."
    elif partial_skills:
        gaps_text = ", ".join(partial_skills)
        gap_sentence = f"Skills needing additional depth include {gaps_text}."
    else:
        if has_reqs or matching_skills:
            gap_sentence = "No specific skill gaps requiring preparation were identified."
        else:
            gap_sentence = ""

    if gap_sentence:
        return f"{first_sentence} {gap_sentence}"

    return first_sentence


def _build_recommendation_prompt(
    job_requirements,
    resume_intelligence,
    resume_analysis,
    skill_gap_analysis,
):
    return f"""
You are the Career Advisor agent in an AI Career Copilot.

Your task is to generate career preparation recommendations
for a candidate based ONLY on the supplied job requirements,
resume evidence, resume analysis and skill-gap analysis.

IMPORTANT RULES:

1. The skill-gap analysis is authoritative.
2. Do not invent missing skills.
3. Do not claim the candidate has a technology that is listed
   as missing or partial.
4. Do not assume that two technologies are equivalent unless
   the supplied evidence explicitly establishes that.
5. Recommendations must be relevant to the supplied job.
6. Recommended topics must be based on identified missing
   or partial skills.
7. Recommended projects must help the candidate practice
   one or more identified gaps.
8. Projects must NOT claim that the candidate has already
   completed them.
9. Do not restrict recommendations to a predefined list of
   technologies. The job may contain any technology,
   framework, platform, database, cloud service or engineering
   practice.
10. Generate recommendations dynamically for the supplied
    skills.
11. Next steps must be actionable and specific to the gaps.
12. Interview preparation must remain evidence-based.
13. Do not recommend unrelated technologies.
14. Do not invent employer requirements.
15. Do not invent candidate experience.
16. Treat each `merged_requirements.canonical_group` as one
    capability. Its `original_names` are terminology aliases,
    not separate gaps to recommend independently.
17. Do not characterize the candidate's applications as monolithic,
    distributed, serverless, or otherwise architected unless the resume
    explicitly establishes that architecture. Describe the demonstrated
    framework or backend work instead.

JOB REQUIREMENTS:
{job_requirements}

RESUME INTELLIGENCE:
{resume_intelligence}

RESUME ANALYSIS:
{resume_analysis}

SKILL GAP ANALYSIS:
{skill_gap_analysis}

Generate a structured CareerRecommendation.

For recommended_topics:
- Cover the important missing and partial skills.
- Preserve the priority indicated by the skill-gap analysis.
- Explain why each topic matters for this job.
- Include the relevant source gap.

For recommended_projects:
- Generate 1-3 practical portfolio projects that help develop the identified gaps.
- Each project should focus on 2-3 related technologies to keep it focused and learnable.
- Group related gaps together (e.g., FastAPI + Microservices, or Azure + Azure Functions).
- Avoid combining every gap into one enormous project.
- Use technologies relevant to the job and the gap.
- Do not claim the candidate has already built these projects.
- A long-running API service (e.g. FastAPI) and serverless
  functions (e.g. Azure Functions) are SEPARATE components
  with distinct roles. Never describe Azure Functions (or any
  serverless platform) as the deployment mechanism for a
  FastAPI service.
- When a project involves both, state the architecture
  explicitly: the FastAPI service handles API/RAG endpoints;
  serverless functions handle event-driven work such as
  document ingestion or background indexing; both may target
  the same downstream store (e.g. Azure AI Search).

For each project, include:
- purpose: A brief statement of what the project demonstrates
- gaps_addressed: List of specific skill gaps this project addresses

For next_steps:
- Give concrete learning and preparation actions.
- Prioritize high-priority gaps before medium-priority gaps.

The output must be specific to this job description and
candidate rather than using generic career advice.
"""


def _validate_topic_recommendations(
    recommendations,
    gap_skills,
):
    """
    Keep only topics that are clearly associated with an
    authoritative gap.
    """
    validated = []

    normalized_gaps = {}

    for skill in gap_skills:
        if not isinstance(skill, str):
            continue

        canonical = canonicalize(skill)

        if canonical:
            normalized_gaps[canonical] = skill

    topics = recommendations or []

    for topic in topics:
        if not isinstance(topic, dict):
            continue

        source_gaps = topic.get("source_gaps", [])

        if not isinstance(source_gaps, list):
            continue

        valid_source_gaps = []

        for source_gap in source_gaps:
            if not isinstance(source_gap, str):
                continue

            canonical_source = canonicalize(source_gap)

            if canonical_source in normalized_gaps:
                canonical_gap = normalized_gaps[canonical_source]

                if canonical_gap not in valid_source_gaps:
                    valid_source_gaps.append(canonical_gap)

        if not valid_source_gaps:
            continue

        topic["source_gaps"] = valid_source_gaps
        validated.append(topic)

    return validated


def _validate_projects(
    projects,
    gap_skills,
    allowed_terms,
):
    """
    Validate recommended projects against both:

    1. Authoritative skill gaps
    2. Supported technologies from the JD/resume/gaps

    A project must address at least one gap and must not
    introduce unrelated technologies.
    """
    validated = []


    for project in projects or []:
        if not isinstance(project, dict):
            continue

        name = project.get(
            "name",
            "",
        )

        description = project.get(
            "description",
            "",
        )

        technologies = project.get(
            "technologies",
            [],
        )

        if not isinstance(technologies, list):
            technologies = []

        project_text = _normalize(
            " ".join(
                [
                    str(name),
                    str(description),
                    *[
                        str(item)
                        for item in technologies
                        if isinstance(item, str)
                    ],
                ]
            )
        )

        # -----------------------------------------
        # 1. Project must relate to a real gap
        # -----------------------------------------

        addresses_gap = False

        for gap in gap_skills:
            if skill_matches(
                project_text,
                gap,
            ):
                addresses_gap = True
                break

        if not addresses_gap:
            continue

        # -----------------------------------------
        # 1b. Project must not introduce unsupported
        #     implementation tools (e.g. Docker) that
        #     are outside the supported vocabulary.
        # -----------------------------------------

        if _mentions_unsupported_tool(
            project_text,
            allowed_terms,
        ):
            continue

        # -----------------------------------------
        # 2. Every named technology must be supported
        # -----------------------------------------

        valid_technologies = []

        for technology in technologies:
            if not isinstance(
                technology,
                str,
            ):
                continue

            technology = technology.strip()

            if not technology:
                continue

            normalized_technology = _normalize(
                technology
            )

            if normalized_technology in allowed_terms:
                valid_technologies.append(
                    technology
            )
                continue

            # Allow a technology label composed of multiple
            # independently supported terms.
            technology_parts = normalized_technology.split()

            if (
                len(technology_parts) > 1
                and all(
                    part in allowed_terms
                    for part in technology_parts
                )
            ):
                valid_technologies.append(
                    technology
                )

        # If the LLM supplied technologies but all of
        # them were unsupported, reject the project.
        if technologies and not valid_technologies:
            continue

        project["technologies"] = valid_technologies

        validated.append(project)

    return validated


# -----------------------------------------
# Implementation-tool registry
# -----------------------------------------
#
# These are generic, frequently-hallucinated implementation
# technologies that LLMs tend to attach to a gap even though the
# job description, resume, and gap analysis never mention them
# (for example "containerization using Docker" attached to a
# Microservices gap).
#
# The list is deliberately technology-agnostic to the JD: a term is
# only rejected when it is NOT part of the supported vocabulary
# (job requirements + resume skills + identified gaps). If a JD
# genuinely requires Docker, `_build_allowed_terms` recognizes it
# and the guard stays silent.
IMPLEMENTATION_TOOL_TERMS = {
    "docker",
    "kubernetes",
    "k8s",
    "terraform",
    "ansible",
    "jenkins",
    "helm",
    "prometheus",
    "grafana",
    "airflow",
    "spark",
    "snowflake",
    "kafka",
    "gitlab",
    "circleci",
    "travis",
    "bitbucket",
    "elasticsearch",
    "sqlalchemy",
}


def _mentions_unsupported_tool(
    text,
    allowed_terms,
):
    """
    Return True when text names an implementation tool that is
    not part of the supported vocabulary.

    A tool is supported when its normalized name (or any of its
    individual words) is present in allowed_terms.
    """
    if not isinstance(text, str):
        return False

    normalized_text = _normalize(text)

    if not normalized_text:
        return False

    if not isinstance(allowed_terms, dict):
        allowed_terms = {}

    for tool in IMPLEMENTATION_TOOL_TERMS:
        if not skill_matches(
            normalized_text,
            tool,
        ):
            continue

        normalized_tool = _normalize(tool)

        if normalized_tool in allowed_terms:
            continue

        # "GitHub Actions"/"Actions on Google" style multi-word
        # labels are acceptable when any constituent word is
        # itself part of the supported vocabulary (e.g. GitHub).
        tool_parts = normalized_tool.split()

        if any(
            part in allowed_terms
            for part in tool_parts
        ):
            continue

        return True

    return False


def _validate_next_steps(
    next_steps,
    gap_skills,
    allowed_terms=None,
):
    """
    Validate next steps against identified gaps.

    A step is retained when its text references at least one
    authoritative gap AND does not introduce an implementation
    tool that is outside the supported vocabulary.
    """
    validated = []

    if allowed_terms is None:
        allowed_terms = {}


    for step in next_steps or []:
        if not isinstance(step, dict):
            continue

        step_text = _normalize(
            step.get("step", "")
        )

        if not step_text:
            continue

        related = False

        for gap in gap_skills:
            if skill_matches(
                step_text,
                gap,
            ):
                related = True
                break

        if not related:
            continue

        if _mentions_unsupported_tool(
            step_text,
            allowed_terms,
        ):
            continue

        validated.append(step)

    return validated

def _extract_gap_priorities(skill_gap_analysis):
    priorities = {}

    for field in [
        "missing_skills",
        "partial_skills",
        "priority_gaps",
    ]:
        items = skill_gap_analysis.get(
            field,
            [],
        )

        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            skill = item.get(
                "skill",
                "",
            )

            priority = item.get(
                "priority",
                "Medium",
            )

            if (
                isinstance(skill, str)
                and isinstance(priority, str)
            ):
                priorities[
                    _normalize(skill)
                ] = priority

    return priorities

def _ensure_gap_coverage(
    recommendations,
    gap_skills,
    gap_priorities,
):
    topics = recommendations or []

    covered = set()

    for topic in topics:
        if not isinstance(topic, dict):
            continue

        for source_gap in topic.get(
            "source_gaps",
            [],
        ):
            if isinstance(source_gap, str):
                canonical = canonicalize(source_gap)

                if canonical:
                    covered.add(canonical)

    for gap in gap_skills:
        canonical_gap = canonicalize(gap)

        if not canonical_gap or canonical_gap in covered:
            continue

        topics.append(
            {
                "topic": gap,
                "priority": gap_priorities.get(
                    _normalize(gap),
                    "Medium",
                ),
                "reason": (
                    "This skill was identified as a "
                    "preparation gap for the target role."
                ),
                "source_gaps": [gap],
            }
        )

        covered.add(canonical_gap)

    return topics


def career_advisor_node(state):
    resume_intelligence = state.get(
        "resume_intelligence",
        {},
    )

    job_requirements = state.get(
        "job_requirements",
        {},
    )

    resume_analysis = state.get(
        "resume_analysis",
        {},
    )

    skill_gap_analysis = state.get(
        "skill_gap_analysis",
        {},
    )

    if not resume_intelligence:
        raise ValueError(
            "Resume Intelligence data is empty."
        )

    if not job_requirements:
        raise ValueError(
            "Job requirements are empty."
        )

    if not resume_analysis:
        raise ValueError(
            "Resume Analysis data is empty."
        )

    if not skill_gap_analysis:
        raise ValueError(
            "Skill Gap Analysis data is empty."
        )

    gap_skills = _extract_gap_items(
        skill_gap_analysis
    )

    allowed_terms = _build_allowed_terms(
        job_requirements=job_requirements,
        resume_intelligence=resume_intelligence,
        gap_skills=gap_skills,
    )

    gap_priorities = _extract_gap_priorities(
        skill_gap_analysis
    )

    
    system_prompt = """
You are an evidence-based Career Advisor agent.

Generate career recommendations from the supplied
job description, resume evidence and skill-gap analysis.

The job description may contain ANY technologies,
frameworks, cloud platforms, databases, programming
languages, engineering practices or domain skills.

Never assume a fixed technology list.

The skill-gap analysis is authoritative.

Do not claim missing or partial skills as existing
experience.

Recommended topics must address identified gaps.

Recommended projects must help the candidate develop
identified gaps.

Next steps must be actionable and gap-specific.

Do not invent candidate experience.
Do not invent job requirements.
"""

    user_prompt = _build_recommendation_prompt(
        job_requirements=job_requirements,
        resume_intelligence=resume_intelligence,
        resume_analysis=resume_analysis,
        skill_gap_analysis=skill_gap_analysis,
    )

    result = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=CareerRecommendation,
        max_retries=2,
    )

    result_data = result.model_dump()

    if not _resume_contains_architecture_evidence(resume_intelligence):
        result_data = _sanitize_architecture_claims(result_data)

    result_data["recommended_topics"] = (
        _validate_topic_recommendations(
            result_data.get(
                "recommended_topics",
                [],
            ),
            gap_skills,
        )
    )

    result_data["recommended_topics"] = (
        _ensure_gap_coverage(
            result_data["recommended_topics"],
            gap_skills,
            gap_priorities,
        )
    )

    result_data["recommended_projects"] = (
        _validate_projects(
            result_data.get(
                "recommended_projects",
                [],
            ),
            gap_skills,
            allowed_terms,
        )
    )

    result_data["next_steps"] = (
        _validate_next_steps(
            result_data.get("next_steps", []),
            gap_skills,
            allowed_terms,
        )
    )

    result_data["match_summary"] = (
        _build_match_summary(
            resume_intelligence,
            skill_gap_analysis,
            job_requirements,
            resume_analysis,
        )
    )

    return {
        "career_recommendation": result_data
    }