from agents.schemas import CareerRecommendation
from agents.services.structured_llm import generate_structured_output
from agents.services.skill_normalizer import (
    normalize_skill,
    skill_matches,
)


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

        if skill and skill not in skills:
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

    missing = _extract_skill_items(
        skill_gap_analysis.get("missing_skills", [])
    )

    partial = _extract_skill_items(
        skill_gap_analysis.get("partial_skills", [])
    )

    for skill in missing + partial:
        if skill not in gaps:
            gaps.append(skill)

    return gaps


def _extract_resume_skills(resume_intelligence):
    """
    Collect technologies explicitly demonstrated by the resume.
    This is used to prevent recommendations from falsely
    claiming that a candidate already has a missing skill.
    """
    skills = []

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

                    if item and item not in skills:
                        skills.append(item)

                elif isinstance(item, dict):
                    for nested_value in item.values():
                        if isinstance(nested_value, str):
                            nested_value = nested_value.strip()

                            if (
                                nested_value
                                and nested_value not in skills
                            ):
                                skills.append(nested_value)

        elif isinstance(value, str):
            value = value.strip()

            if value and value not in skills:
                skills.append(value)

    return skills


def _extract_project_names(resume_intelligence):
    """
    Extract actual project names from the resume.
    """
    projects = []

    resume_projects = resume_intelligence.get(
        "projects",
        [],
    )

    if not isinstance(resume_projects, list):
        return projects

    for project in resume_projects:
        if not isinstance(project, dict):
            continue

        name = project.get("name")

        if not isinstance(name, str):
            continue

        name = name.strip()

        if name and name not in projects:
            projects.append(name)

    return projects

def _collect_strings(value):
    """
    Recursively collect meaningful strings from dictionaries
    and lists.
    """
    results = []

    if isinstance(value, str):
        value = value.strip()

        if value:
            results.append(value)

    elif isinstance(value, list):
        for item in value:
            results.extend(
                _collect_strings(item)
            )

    elif isinstance(value, dict):
        for nested_value in value.values():
            results.extend(
                _collect_strings(nested_value)
            )

    return results


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

    # Job requirements - only required/preferred skills
    if isinstance(job_requirements, dict):
        for field in ["required_skills", "preferred_skills"]:
            skills = job_requirements.get(field, [])
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, str):
                        skill = skill.strip()
                        if skill:
                            allowed_terms.append(skill)

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


def _contains_supported_term(
    text,
    allowed_terms,
):
    """
    Check whether a piece of recommendation text contains
    at least one supported technology/skill.
    """
    if not isinstance(text, str):
        return False

    normalized_text = _normalize(text)

    if not normalized_text:
        return False

    for normalized_term in allowed_terms:
        if not normalized_term:
            continue

        if normalized_term in normalized_text:
            return True

    return False

def _build_match_summary(
    resume_intelligence,
    skill_gap_analysis,
    job_requirements,
):
    """
    Build a factual match summary that is JD-aware.

    Prioritizes skills that are both demonstrated AND
    relevant to the job requirements.
    """
    resume_skills = _extract_resume_skills(resume_intelligence)
    gaps = _extract_gap_items(skill_gap_analysis)

    # Get job's required/preferred skills
    job_skills = set()
    if isinstance(job_requirements, dict):
        for field in ["required_skills", "preferred_skills"]:
            skills = job_requirements.get(field, [])
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, str):
                        skill = skill.strip()
                        if skill:
                            job_skills.add(_normalize(skill))

    # Score resume skills by JD relevance
    scored_skills = []
    for skill in resume_skills:
        normalized = _normalize(skill)
        if normalized in job_skills:
            scored_skills.append((skill, 2))  # Direct match
        elif any(jd_skill in normalized or normalized in jd_skill for jd_skill in job_skills):
            scored_skills.append((skill, 1))  # Partial match

    # Sort by relevance score, then take top skills
    scored_skills.sort(key=lambda x: (-x[1], x[0]))
    demonstrated = [s[0] for s in scored_skills[:10]]

    if not demonstrated:
        demonstrated = resume_skills[:10]

    if demonstrated:
        demonstrated_text = ", ".join(demonstrated)
    else:
        demonstrated_text = "No specific technologies were extracted"

    if gaps:
        gaps_text = ", ".join(gaps)
        gap_sentence = f"Key preparation areas include {gaps_text}."
    else:
        gap_sentence = "No specific skill gaps requiring preparation were identified."

    return f"The candidate demonstrates experience in {demonstrated_text}. {gap_sentence}"


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
- Generate practical portfolio projects that help develop
  the identified gaps.
- Projects may combine multiple related gaps when that is
  logically useful.
- Use technologies relevant to the job and the gap.
- Do not claim the candidate has already built these projects.

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

    This prevents the LLM from adding unrelated technologies.
    """
    validated = []

    normalized_gaps = {
        _normalize(skill): skill
        for skill in gap_skills
        if isinstance(skill, str)
    }

    topics = recommendations or []

    for topic in topics:
        if not isinstance(topic, dict):
            continue

        source_gaps = topic.get(
            "source_gaps",
            [],
        )

        if not isinstance(source_gaps, list):
            continue

        valid_source_gaps = []

        for source_gap in source_gaps:
            if not isinstance(source_gap, str):
                continue

            normalized_source = _normalize(
                source_gap
            )

            if normalized_source in normalized_gaps:
                canonical_gap = normalized_gaps[
                    normalized_source
                ]

                if canonical_gap not in valid_source_gaps:
                    valid_source_gaps.append(
                        canonical_gap
                    )

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

    normalized_gaps = [
        _normalize(skill)
        for skill in gap_skills
        if isinstance(skill, str)
    ]

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


def _validate_next_steps(
    next_steps,
    gap_skills,
):
    """
    Validate next steps against identified gaps.

    A step is retained when its text references at least one
    authoritative gap.
    """
    validated = []

    normalized_gaps = [
        _normalize(skill)
        for skill in gap_skills
        if isinstance(skill, str)
    ]

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

        if related:
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
                covered.add(
                    _normalize(source_gap)
                )

    for gap in gap_skills:
        normalized_gap = _normalize(gap)

        if normalized_gap in covered:
            continue

        topics.append(
            {
                "topic": gap,
                "priority": gap_priorities.get(
                    normalized_gap,
                    "Medium",
                ),
                "reason": (
                    "This skill was identified as a "
                    "preparation gap for the target role."
                ),
                "source_gaps": [gap],
            }
        )

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
            result_data.get(
                "next_steps",
                [],
            ),
            gap_skills,
        )
    )

    result_data["match_summary"] = (
        _build_match_summary(
            resume_intelligence,
            skill_gap_analysis,
            job_requirements,
        )
    )

    return {
        "career_recommendation": result_data
    }