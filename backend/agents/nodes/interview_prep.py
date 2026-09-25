from agents.schemas import InterviewPreparationPlan
from agents.services.structured_llm import generate_structured_output
from agents.services.skill_normalizer import (
    skill_matches,
)
from agents.services.skill_matching import canonicalize

def _normalize(value):
    if not isinstance(value, str):
        return ""

    return " ".join(
        value.lower().strip().split()
    )

def _contains_term(text, term):
    return skill_matches(
        text,
        term,
    )

def _extract_skill_names(items):
    skills = []

    if not isinstance(items, list):
        return skills

    for item in items:
        if isinstance(item, dict):
            skill = item.get("skill")
        elif isinstance(item, str):
            skill = item
        else:
            skill = None

        if not isinstance(skill, str):
            continue

        skill = skill.strip()

        if skill and skill not in skills:
            skills.append(skill)

    return skills


def _extract_project_names(resume_intelligence):
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


def _extract_resume_evidence(resume_intelligence):
    """
    Extract text that can be used to ground behavioral
    and project-related interview questions.
    """

    evidence = []

    for field in [
        "summary",
        "professional_summary",
        "experience",
        "work_experience",
        "skills",
        "programming_languages",
        "frameworks",
        "ai_ml_technologies",
        "tools",
        "responsibilities",
    ]:
        value = resume_intelligence.get(field)

        if isinstance(value, str):
            if value.strip():
                evidence.append(value.strip())

        elif isinstance(value, list):
            for item in value:

                if isinstance(item, str):
                    if item.strip():
                        evidence.append(item.strip())

                elif isinstance(item, dict):
                    for nested_value in item.values():

                        if isinstance(nested_value, str):
                            if nested_value.strip():
                                evidence.append(
                                    nested_value.strip()
                                )

    return evidence


def _question_mentions_gap(
    question,
    gap_skills,
):
    if not isinstance(question, str):
        return False

    for skill in gap_skills:
        if skill_matches(
            question,
            skill,
        ):
            return True

    return False

def _question_mentions_project(
    question,
    project_names,
):
    if not isinstance(question, str):
        return False

    question_lower = _normalize(question)

    for project in project_names:

        project_lower = _normalize(project)

        if not project_lower:
            continue

        if project_lower in question_lower:
            return True

    return False


def _contains_unapproved_technology(
    question,
    allowed_terms,
):
    """
    Return True when a question introduces a known
    technology that is not present in the allowed vocabulary.
    """

    if not isinstance(question, str):
        return True

    if not isinstance(allowed_terms, list):
        return True

    # Known technology terms that should be checked when
    # they appear in generated interview questions.
    technology_terms = {
        "docker",
        "kubernetes",
        "k8s",
        "terraform",
        "ansible",
        "jenkins",
        "github actions",
        "gitlab ci",
        "azure devops",
        "aws",
        "azure",
        "gcp",
        "kafka",
        "airflow",
        "spark",
        "snowflake",
        "elasticsearch",
        "sqlalchemy",
        "helm",
        "prometheus",
        "grafana",
    }

    normalized_allowed = {
        _normalize(term)
        for term in allowed_terms
        if isinstance(term, str) and term.strip()
    }

    for technology in technology_terms:
        if not skill_matches(question, technology):
            continue

        normalized_technology = _normalize(technology)

        if normalized_technology not in normalized_allowed:
            return True

    return False


def _clean_gap_questions(
    questions,
    gap_skills,
    allowed_terms,
):
    cleaned = []

    if not isinstance(questions, list):
        return cleaned

    seen_questions = set()

    for question in questions:

        if not isinstance(question, dict):
            continue

        question_text = question.get(
            "question",
            "",
        )

        if not isinstance(question_text, str):
            continue

        question_text = question_text.strip()

        if not question_text:
            continue

        if not _question_mentions_gap(
            question_text,
            gap_skills,
        ):
            continue

        if _contains_unapproved_technology(
            question_text,
            allowed_terms,
        ):
            continue

        if _is_experience_question_for_gap(
            question_text,
            gap_skills,
        ):
            continue

        normalized_question = _normalize(
            question_text
        )

        if normalized_question in seen_questions:
            continue

        question["category"] = "Gap-Based"

        seen_questions.add(
            normalized_question
        )

        cleaned.append(question)

    return cleaned


def _clean_project_questions(
    questions,
    project_names,
    allowed_terms,
):
    cleaned = []

    if not isinstance(questions, list):
        return cleaned

    seen_questions = set()

    for question in questions:

        if not isinstance(question, dict):
            continue

        question_text = question.get(
            "question",
            "",
        )

        if not isinstance(question_text, str):
            continue

        question_text = question_text.strip()

        if not question_text:
            continue

        if not _question_mentions_project(
            question_text,
            project_names,
        ):
            continue

        if _contains_unapproved_technology(
            question_text,
            allowed_terms,
        ):
            continue

        normalized_question = _normalize(
            question_text
        )

        if normalized_question in seen_questions:
            continue

        question["category"] = "Project"

        seen_questions.add(
            normalized_question
        )

        cleaned.append(question)

    return cleaned

def _is_gap_question(question, gap_skills):
    if not isinstance(question, str):
        return False

    return _question_mentions_gap(
        question,
        gap_skills,
    )

def _clean_technical_questions(
    questions,
    allowed_terms,
    gap_skills,
):
    cleaned = []

    if not isinstance(questions, list):
        return cleaned

    seen_questions = set()

    for question in questions:

        if not isinstance(question, dict):
            continue

        question_text = question.get(
            "question",
            "",
        )

        if not isinstance(question_text, str):
            continue

        question_text = question_text.strip()

        if not question_text:
            continue

        if _contains_unapproved_technology(
            question_text,
            allowed_terms,
        ):
            continue

        if _is_experience_question_for_gap(
            question_text,
            gap_skills,
        ):
            continue

        if _is_gap_question(
            question_text,
            gap_skills,
        ):
            continue

        normalized_question = _normalize(
            question_text
        )

        if normalized_question in seen_questions:
            continue

        question["category"] = "Technical"

        seen_questions.add(
            normalized_question
        )

        cleaned.append(question)

    return cleaned


def _clean_behavioral_questions(
    questions,
):
    """
    Behavioral questions are intentionally conservative.

    We remove questions that require unsupported personal
    experiences such as:

    - managing teams
    - resolving team conflicts
    - leading projects
    - managing stakeholders

    unless the resume explicitly provides evidence for them.
    """

    cleaned = []

    if not isinstance(questions, list):
        return cleaned

    seen_questions = set()

    unsupported_patterns = [
        "manage a team",
        "managed a team",
        "lead a team",
        "led a team",
        "team conflict",
        "conflict with a teammate",
        "conflict with a team member",
        "manage stakeholders",
        "managed stakeholders",
        "led a project",
        "managed a project",
        "leadership experience",
        "management experience",
    ]

    for question in questions:

        if not isinstance(question, dict):
            continue

        question_text = question.get(
            "question",
            "",
        )

        if not isinstance(question_text, str):
            continue

        question_text = question_text.strip()

        if not question_text:
            continue

        question_lower = _normalize(
            question_text
        )

        unsupported = False

        for pattern in unsupported_patterns:

            if pattern in question_lower:
                unsupported = True
                break

        if unsupported:
            continue

        if question_lower in seen_questions:
            continue

        question["category"] = "Behavioral"

        seen_questions.add(
            question_lower
        )

        cleaned.append(question)

    return cleaned


def _clean_preparation_topics(
    topics,
    gap_skills,
):
    """
    Preparation topics are restricted to the actual
    Skill Gap Analysis.
    """

    if not isinstance(topics, list):
        return []

    cleaned = []

    normalized_gaps = {
        _normalize(gap): gap
        for gap in gap_skills
    }

    for topic in topics:

        if not isinstance(topic, str):
            continue

        topic = topic.strip()

        if not topic:
            continue

        topic_lower = _normalize(topic)

        for normalized_gap, original_gap in normalized_gaps.items():

            if (
                topic_lower == normalized_gap
                or normalized_gap in topic_lower
                or topic_lower in normalized_gap
            ):
                if original_gap not in cleaned:
                    cleaned.append(original_gap)

                break

    return cleaned


def _build_fallback_behavioral_questions(
    resume_intelligence,
):
    """
    Build behavioral questions from evidence explicitly
    present in the resume.
    """

    evidence = " ".join(
        _extract_resume_evidence(
            resume_intelligence
        )
    ).lower()

    questions = []

    if (
        "debug" in evidence
        or "troubleshoot" in evidence
        or "issue" in evidence
    ):
        questions.append(
            {
                "question": (
                    "Can you describe a backend issue you "
                    "worked on and how you approached debugging it?"
                ),
                "category": "Behavioral",
                "difficulty": "Medium",
                "reason": (
                    "The resume explicitly contains debugging "
                    "and troubleshooting experience."
                ),
            }
        )

    if "code review" in evidence:
        questions.append(
            {
                "question": (
                    "How do you approach receiving and applying "
                    "feedback during code review?"
                ),
                "category": "Behavioral",
                "difficulty": "Easy",
                "reason": (
                    "The resume explicitly mentions participation "
                    "in code reviews."
                ),
            }
        )

    if (
        "self-study" in evidence
        or "learning" in evidence
        or "learn" in evidence
    ):
        questions.append(
            {
                "question": (
                    "How do you approach learning a technology "
                    "that is required for a new development task?"
                ),
                "category": "Behavioral",
                "difficulty": "Easy",
                "reason": (
                    "The resume explicitly mentions an active "
                    "self-study and technical learning track."
                ),
            }
        )

    return questions[:3]

def _build_fallback_technical_questions(
    resume_intelligence,
    gap_skills,
):
    """
    Build technical interview questions only from technologies
    explicitly demonstrated by the resume.

    Authoritative skill gaps are always excluded.
    """

    gap_normalized = {
        _normalize(skill)
        for skill in gap_skills
        if isinstance(skill, str)
    }

    resume_skills = set()

    for field in [
        "skills",
        "programming_languages",
        "frameworks",
        "tools",
        "databases",
        "ai_ml_technologies",
    ]:
        value = resume_intelligence.get(
            field,
            [],
        )

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    resume_skills.add(
                        _normalize(item)
                    )

                elif isinstance(item, dict):
                    skill = item.get("skill")

                    if isinstance(skill, str):
                        resume_skills.add(
                            _normalize(skill)
                        )

    questions = []

    def is_gap(skill):
        return _normalize(skill) in gap_normalized

    def is_demonstrated(skill):
        normalized_skill = _normalize(skill)

        return any(
            skill_matches(
                resume_skill,
                normalized_skill,
            )
            for resume_skill in resume_skills
        )

    if is_demonstrated("Django") and not is_gap("Django"):
        questions.append(
            {
                "question": (
                    "How would you design a REST API using "
                    "Django REST Framework?"
                ),
                "category": "Technical",
                "difficulty": "Medium",
                "reason": (
                    "The resume explicitly demonstrates backend "
                    "development using Django and Django REST Framework."
                ),
            }
        )

    if is_demonstrated("SQL") and not is_gap("SQL"):
        questions.append(
            {
                "question": (
                    "How would you troubleshoot and optimize "
                    "a SQL query that is performing slowly?"
                ),
                "category": "Technical",
                "difficulty": "Medium",
                "reason": (
                    "The resume explicitly demonstrates SQL and "
                    "relational database experience."
                ),
            }
        )

    if is_demonstrated("WebSockets") and not is_gap("WebSockets"):
        questions.append(
            {
                "question": (
                    "How would you design real-time communication "
                    "using WebSockets in a backend application?"
                ),
                "category": "Technical",
                "difficulty": "Medium",
                "reason": (
                    "The resume explicitly demonstrates WebSockets "
                    "and real-time communication."
                ),
            }
        )

    if is_demonstrated("REST APIs") and not is_gap("REST APIs"):
        questions.append(
            {
                "question": (
                    "What are the key considerations when designing "
                    "a maintainable REST API?"
                ),
                "category": "Technical",
                "difficulty": "Medium",
                "reason": (
                    "The resume explicitly demonstrates REST API "
                    "development."
                ),
            }
        )

    if is_demonstrated("Python") and not is_gap("Python"):
        questions.append(
            {
                "question": (
                    "How would you troubleshoot a backend issue "
                    "in a Python application?"
                ),
                "category": "Technical",
                "difficulty": "Medium",
                "reason": (
                    "The resume explicitly demonstrates Python "
                    "backend development and debugging."
                ),
            }
        )

    return questions[:5]

def _build_allowed_terms(
    resume_intelligence,
    job_requirements,
    gap_skills,
    project_names,
):
    """
    Build the vocabulary of technologies/concepts that the
    Interview Prep agent is allowed to mention.
    """

    allowed_terms = []

    allowed_terms.extend(gap_skills)
    allowed_terms.extend(project_names)

    # Job requirements
    for field in [
        "required_skills",
        "preferred_skills",
        "responsibilities",
        "technical_requirements",
    ]:
        value = job_requirements.get(field, [])

        if isinstance(value, list):
            for item in value:

                if isinstance(item, str):
                    allowed_terms.append(item)

                elif isinstance(item, dict):
                    display_name = item.get(
                        "display_name",
                    ) or item.get("skill")
                    original_names = item.get(
                        "original_names",
                        [],
                    )

                    if isinstance(display_name, str):
                        allowed_terms.append(
                            display_name
                        )

                    if isinstance(original_names, list):
                        allowed_terms.extend(
                            value
                            for value in original_names
                            if isinstance(value, str)
                        )

        elif isinstance(value, str):
            allowed_terms.append(value)

    # Authoritative requirement registry
    registry = job_requirements.get(
        "requirement_registry",
        [],
    )

    if isinstance(registry, list):
        for item in registry:
            if not isinstance(item, dict):
                continue

            display_name = (
                item.get("display_name")
                or item.get("skill")
            )

            if isinstance(display_name, str):
                display_name = display_name.strip()

                if display_name:
                    allowed_terms.append(
                        display_name
                    )

            original_names = item.get(
                "original_names",
                [],
            )

            if isinstance(original_names, list):
                for value in original_names:
                    if (
                        isinstance(value, str)
                        and value.strip()
                    ):
                        allowed_terms.append(
                            value.strip()
                        )

    # Resume technologies
    for field in [
        "skills",
        "programming_languages",
        "frameworks",
        "ai_ml_technologies",
        "tools",
        "databases",
    ]:
        value = resume_intelligence.get(field, [])

        if isinstance(value, list):
            for item in value:

                if isinstance(item, str):
                    allowed_terms.append(item)

                elif isinstance(item, dict):
                    for nested_value in item.values():

                        if isinstance(
                            nested_value,
                            str,
                        ):
                            allowed_terms.append(
                                nested_value
                            )

        elif isinstance(value, str):
            allowed_terms.append(value)

    return allowed_terms


def _is_experience_question_for_gap(
    question,
    gap_skills,
):
    """
    Detect questions that incorrectly ask the candidate
    about previous experience with a missing skill.
    """

    if not isinstance(question, str):
        return False

    question_lower = _normalize(question)

    experience_patterns = [
        "your experience with",
        "your experience in",
        "describe your experience",
        "what is your experience",
        "how have you used",
        "how have you implemented",
        "have you used",
        "have you implemented",
        "tell me about your experience",
        "describe how you used",
        "describe how you implemented",
        "a scenario where you had to",
        "a situation where you had to",
        "when you implemented",
        "when have you implemented",
        "how did you implement",
        "how did you use",
        "what tools do you use",
    ]

    contains_experience_pattern = any(
        pattern in question_lower
        for pattern in experience_patterns
    )

    if not contains_experience_pattern:
        return False

    for skill in gap_skills:

        if _contains_term(
            question_lower,
            skill,
        ):
            return True

    return False


def _build_missing_gap_questions(
    existing_questions,
    gap_skills,
):
    fallback_questions = []

    fallback_map = {
        "java": (
            "How would you design a simple Java backend service "
            "using object-oriented programming and exception handling?"
        ),
        "microservices": (
            "How would you design communication between "
            "two independently deployable microservices while "
            "maintaining clear service boundaries?"
        ),
        "continuous integration": (
            "How would you design a continuous integration "
            "workflow for a software project?"
        ),
        "automated build and deployment pipelines": (
            "How would you design an automated build, testing "
            "and deployment pipeline?"
        ),
        "asset and wealth management processes": (
            "Can you explain the basic workflow of portfolios, "
            "holdings and investment transactions?"
        ),
    }

    for skill in gap_skills:

        normalized_skill = _normalize(skill)

        already_covered = False

        for question in existing_questions:

            if not isinstance(question, dict):
                continue

            question_text = question.get(
                "question",
                "",
            )

            if not isinstance(question_text, str):
                continue

            if _question_mentions_gap(
                question_text,
                [skill],
            ):
                already_covered = True
                break

        if already_covered:
            continue

        question_text = fallback_map.get(
            normalized_skill
        )

        if not question_text:
            continue

        fallback_questions.append(
            {
                "question": question_text,
                "category": "Gap-Based",
                "difficulty": "Medium",
                "reason": (
                    "The job requirement is not explicitly "
                    "demonstrated in the resume, so the question "
                    "assesses foundational understanding."
                ),
            }
        )

    combined = (
        existing_questions
        + fallback_questions
    )

    cleaned = []
    seen = set()

    for question in combined:

        if not isinstance(question, dict):
            continue

        question_text = question.get(
            "question",
            "",
        )

        if not isinstance(question_text, str):
            continue

        normalized = _normalize(
            question_text
        )

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append(question)

    return cleaned[:8]

def interview_prep_node(state):

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

    # ==================================================
    # AUTHORITATIVE SKILL GAPS
    # ==================================================

    missing_skills = _extract_skill_names(
        skill_gap_analysis.get(
            "missing_skills",
            [],
        )
    )

    partial_skills = _extract_skill_names(
        skill_gap_analysis.get(
            "partial_skills",
            [],
        )
    )

    gap_skills = []
    seen = set()

    for skill in missing_skills + partial_skills:
        canonical = canonicalize(skill)
        if canonical and canonical in seen:
            continue
        if canonical:
            seen.add(canonical)
        gap_skills.append(skill)

    # ==================================================
    # ACTUAL RESUME PROJECTS
    # ==================================================

    project_names = _extract_project_names(
        resume_intelligence
    )

    # ==================================================
    # ALLOWED VOCABULARY
    # ==================================================

    allowed_terms = _build_allowed_terms(
        resume_intelligence,
        job_requirements,
        gap_skills,
        project_names,
    )

    # ==================================================
    # SYSTEM PROMPT
    # ==================================================

    system_prompt = """
You are the Interview Preparation agent in an AI Career Copilot.

Generate an evidence-based interview preparation plan.

The candidate's resume is authoritative for demonstrated experience.

The Skill Gap Analysis is authoritative for missing skills.

==================================================
CRITICAL EVIDENCE RULE
==================================================

Never claim that the candidate has experience with a skill merely because
the skill appears in the job description.

If a skill is missing, ask a knowledge, design, implementation, or learning
question instead of asking the candidate to describe experience they do not
have.

==================================================
NO INVENTED TECHNOLOGIES
==================================================

Do NOT introduce specific tools, platforms, frameworks or technologies
unless they are explicitly present in one of:

1. Resume Intelligence
2. Job Requirements
3. Skill Gap Analysis

For example, do NOT introduce:

Jenkins
Docker
Kubernetes
GitHub Actions
GitLab CI
Azure DevOps
Terraform
AWS
Azure
GCP

unless they are explicitly present in the supplied evidence.

==================================================
TECHNICAL QUESTIONS
==================================================

Generate 5-8 questions.

Questions should be relevant to the job requirements and resume.

For demonstrated technologies, questions may ask about implementation
or experience.

For missing technologies, ask knowledge/design/implementation questions.

==================================================
PROJECT QUESTIONS
==================================================

Generate 3-5 questions.

ONLY reference projects explicitly present in the resume.

Do not invent project names or project functionality.

==================================================
GAP-BASED QUESTIONS
==================================================

Generate 5-8 questions.

Use ONLY these authoritative gaps:

<GAP_SKILLS>

For missing skills, ask knowledge/design/implementation questions.

Do NOT ask questions that imply the candidate has already used
the missing skill.

Avoid wording such as:

- "in your projects"
- "in your project"
- "in a project"
- "how did you implement"
- "how have you implemented"
- "what tools do you use"
- "describe a scenario where you implemented"
- "describe your experience with"

Prefer wording such as:

- "How would you design..."
- "How would you implement..."
- "What are the key concepts..."
- "How does ... work?"
- "What considerations should be made when..."
- "How would you approach..."

Do not ask the candidate to describe previous experience with a missing skill.

==================================================
BEHAVIORAL QUESTIONS
==================================================

Generate 3-5 questions.

Use general behavioral questions or situations supported by the resume.

Do not invent:

- leadership experience
- team management
- stakeholder management
- conflict resolution experience
- project management experience

==================================================
PREPARATION TOPICS
==================================================

Return ONLY the authoritative skill gaps:

<GAP_SKILLS>

==================================================
OUTPUT
==================================================

Return exactly:

{
    "technical_questions": [],
    "project_questions": [],
    "gap_based_questions": [],
    "behavioral_questions": [],
    "preparation_topics": []
}

Every question must contain:

{
    "question": "string",
    "category": "string",
    "difficulty": "string",
    "reason": "string"
}

Return ONLY valid JSON.
"""

    system_prompt = system_prompt.replace(
        "<GAP_SKILLS>",
        str(gap_skills),
    )

    # ==================================================
    # USER PROMPT
    # ==================================================

    user_prompt = f"""
Create an interview preparation plan for this candidate.

RESUME INTELLIGENCE:
{resume_intelligence}

JOB REQUIREMENTS:
{job_requirements}

RESUME ANALYSIS:
{resume_analysis}

AUTHORITATIVE SKILL GAP ANALYSIS:
{skill_gap_analysis}

AUTHORITATIVE GAP SKILLS:
{gap_skills}

ACTUAL RESUME PROJECTS:
{project_names}

IMPORTANT:

Gap-based questions may ONLY cover:

{gap_skills}

Preparation topics may ONLY contain:

{gap_skills}

Project questions may ONLY reference:

{project_names}

Do not introduce technologies or tools that are not present
in the supplied resume, job requirements or skill gaps.

Do not claim experience with missing skills.

Return ONLY valid JSON.
"""

    # ==================================================
    # LLM GENERATION
    # ==================================================

    result = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=InterviewPreparationPlan,
        max_retries=2,
    )

    result_data = result

    # ==================================================
    # DETERMINISTIC VALIDATION
    # ==================================================

    result_data["technical_questions"] = (
        _clean_technical_questions(
            result_data.get(
                "technical_questions",
                [],
            ),
            allowed_terms,
            gap_skills,
        )
    )

    if len(result_data["technical_questions"]) < 5:
        fallback_technical = (
            _build_fallback_technical_questions(
                resume_intelligence,
                gap_skills,
            )
        )

        combined = (
            result_data["technical_questions"]
            + fallback_technical
        )

        cleaned = []
        seen = set()

        for question in combined:
            question_text = question.get("question", "")

            normalized = _normalize(question_text)

            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(question)

        result_data["technical_questions"] = cleaned[:5]

    result_data["gap_based_questions"] = (
        _clean_gap_questions(
            result_data.get(
                "gap_based_questions",
                [],
            ),
            gap_skills,
            allowed_terms,
        )
    )
    result_data["gap_based_questions"] = (
        _build_missing_gap_questions(
            result_data["gap_based_questions"],
            gap_skills,
        )
    )

    result_data["project_questions"] = (
        _clean_project_questions(
            result_data.get(
                "project_questions",
                [],
            ),
            project_names,
            allowed_terms,
        )
    )

    result_data["behavioral_questions"] = (
        _clean_behavioral_questions(
            result_data.get(
                "behavioral_questions",
                [],
            )
        )
    )

    result_data["preparation_topics"] = (
        _clean_preparation_topics(
            result_data.get(
                "preparation_topics",
                [],
            ),
            gap_skills,
        )
    )

    # ==================================================
    # FALLBACK PREPARATION TOPICS
    # ==================================================

    if not result_data["preparation_topics"]:
        result_data["preparation_topics"] = (
            gap_skills.copy()
        )

    # ==================================================
    # FALLBACK BEHAVIORAL QUESTIONS
    # ==================================================

    if len(result_data["behavioral_questions"]) < 3:
        fallback_behavioral = (
            _build_fallback_behavioral_questions(
                resume_intelligence
            )
        )

        existing_questions = (
            result_data["behavioral_questions"]
        )

        combined = (
            existing_questions
            + fallback_behavioral
        )

        cleaned = []
        seen = set()

        for question in combined:
            if not isinstance(question, dict):
                continue

            question_text = question.get(
                "question",
                "",
            )

            if not isinstance(question_text, str):
                continue

            normalized = _normalize(
                question_text
            )

            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(question)

        result_data["behavioral_questions"] = cleaned[:3]

    return {
        "interview_preparation": result_data
    }