from typing import Literal

from pydantic import BaseModel

from agents.schemas import SkillGapAnalysis
from agents.services.structured_llm import (
    generate_structured_output,
)
from agents.services.skill_matching import (
    build_candidate_evidence,
    build_resume_evidence_text,
    canonicalize,
    classify_requirement,
)

from agents.services.skill_normalizer import (
    skill_matches,
)

class SemanticGapDecision(BaseModel):
    skill: str
    classification: Literal["partial", "missing"]


class SemanticGapClassification(BaseModel):
    decisions: list[SemanticGapDecision]

def classify_semantic_gaps(
    requirements,
    resume_intelligence,
    resume_analysis,
):
    """
    Determine whether requirements that are not explicitly
    demonstrated have related resume evidence.

    The LLM is only allowed to return:
        partial
        missing

    It can NEVER return demonstrated.

    Exact/equivalent matching remains deterministic.
    """

    if not requirements:
        return {}

    system_prompt = """
You are a conservative skill-gap classification engine.

Your task is to determine whether each job requirement that is NOT
explicitly demonstrated by the candidate has RELATED but incomplete
evidence in the resume.

There are only two possible classifications:

- partial
- missing

IMPORTANT:

You are NOT allowed to classify anything as demonstrated.

A requirement is PARTIAL only when the resume contains meaningful,
technically relevant evidence that is related to the requirement but
does not prove the exact requirement.

A requirement is MISSING when the resume does not contain meaningful
related evidence.

Do NOT treat generic programming knowledge as related evidence.

Do NOT treat unrelated technologies as related.

Examples:

Django -> FastAPI
missing or partial depending on evidence, but NEVER demonstrated.

Python -> Java
missing.

PostgreSQL -> MongoDB
missing.

RAG + vector search -> Azure AI Search
potentially partial because the technical concepts are related,
but Azure-specific experience is not demonstrated.

Git -> CI/CD
missing.

REST APIs -> FastAPI
potentially partial only if the resume contains meaningful API/backend
experience relevant to the requirement.

React -> ReactJS
this should normally have already been handled by deterministic
matching and should not be supplied here.

Do not invent resume experience.

Return one decision for every supplied requirement.

Return ONLY valid JSON.
"""

    user_prompt = f"""
REQUIREMENTS TO CLASSIFY:

{requirements}

RESUME INTELLIGENCE:

{resume_intelligence}

RESUME ANALYSIS:

{resume_analysis}

For every supplied requirement return an object containing:

- skill: the exact supplied requirement
- classification: either "partial" or "missing"

Do not return demonstrated.
Do not omit any supplied requirement.
"""

    result = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=SemanticGapClassification,
        max_retries=1,
    )

    decisions = {}

    for decision in result.decisions:

        if not isinstance(decision.skill, str):
            continue

        skill_key = canonicalize(
            decision.skill
        )

        if not skill_key:
            continue

        if decision.classification not in {
            "partial",
            "missing",
        }:
            continue

        decisions[skill_key] = (
            decision.classification
        )

    return decisions

def skill_gap_node(state):

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

    # -----------------------------------------------------
    # Build explicit candidate evidence
    # -----------------------------------------------------

    candidate_evidence = build_candidate_evidence(
        resume_intelligence
    )

    resume_evidence_text = build_resume_evidence_text(
        resume_intelligence
    )

    # -----------------------------------------------------
    # Resume Analyzer is authoritative for demonstrated
    # matching skills.
    #
    # Canonicalize them so terminology such as:
    #
    # Git -> Source control
    # Version control -> Source control
    #
    # remains consistent downstream.
    # -----------------------------------------------------

    confirmed_matches = {
        canonicalize(skill)
        for skill in resume_analysis.get(
            "matching_skills",
            [],
        )
        if isinstance(skill, str)
    }

    # -----------------------------------------------------
    # Job requirements
    # -----------------------------------------------------

    required_skills = job_requirements.get(
        "required_skills",
        [],
    )

    preferred_skills = job_requirements.get(
        "preferred_skills",
        [],
    )

    # -----------------------------------------------------
    # Classification containers
    # -----------------------------------------------------

    missing_skills = []
    partial_skills = []
    priority_gaps = []

    processed = set()

    # -----------------------------------------------------
    # Deterministic + semantic classification
    # -----------------------------------------------------

    semantic_candidates = []

    for requirement in (
        required_skills + preferred_skills
    ):

        canonical_requirement = canonicalize(
            requirement
        )

        if not canonical_requirement:
            continue

        if canonical_requirement in processed:
            continue

        # Resume Analyzer already confirmed it.
        if any(
            skill_matches(
                canonical_requirement,
                confirmed_skill,
            )
            for confirmed_skill in confirmed_matches
        ):
            continue

        deterministic_classification = (
            classify_requirement(
                requirement=requirement,
                candidate_evidence=candidate_evidence,
                confirmed_matches=confirmed_matches,
                resume_text=resume_evidence_text,
            )
        )

        # Only requirements that deterministic matching considers
        # missing are sent to semantic analysis.
        #
        # Existing deterministic partial relationships remain
        # valid and do not need an additional LLM call.
        if deterministic_classification == "missing":
            semantic_candidates.append(
                requirement
            )

    semantic_decisions = classify_semantic_gaps(
        requirements=semantic_candidates,
        resume_intelligence=resume_intelligence,
        resume_analysis=resume_analysis,
    )

    # -----------------------------------------------------
    # Helper
    # -----------------------------------------------------

    def process_requirement(
        requirement,
        source,
    ):

        canonical_requirement = canonicalize(
            requirement
        )

        # Avoid duplicate requirements such as:
        # FastAPI + Fast API
        if canonical_requirement in processed:
            return

        processed.add(canonical_requirement)

        # -------------------------------------------------
        # AUTHORITATIVE MATCH
        # -------------------------------------------------
        #
        # If Resume Analyzer explicitly confirmed this
        # requirement as a matching skill, it is
        # demonstrated.
        #
        # Do NOT allow classify_requirement() to override it.
        # -------------------------------------------------

        if any(
            skill_matches(
                canonical_requirement,
                confirmed_skill,
            )
            for confirmed_skill in confirmed_matches
        ):
            return

        # -------------------------------------------------
        # For everything not explicitly confirmed by the
        # Resume Analyzer, use the evidence classifier to
        # determine whether the requirement is partial or
        # missing.
        # -------------------------------------------------

        deterministic_classification = (
            classify_requirement(
                requirement=requirement,
                candidate_evidence=candidate_evidence,
                confirmed_matches=confirmed_matches,
                resume_text=resume_evidence_text,
            )
        )

        if deterministic_classification == "demonstrated":
            classification = "demonstrated"

        elif deterministic_classification == "partial":
            classification = "partial"

        else:
            classification = semantic_decisions.get(
                canonical_requirement,
                "missing",
            )

        # ---------------------------------------------
        # Demonstrated
        # ---------------------------------------------

        if classification == "demonstrated":
            return

        # ---------------------------------------------
        # Partial
        # ---------------------------------------------

        if classification == "partial":

            priority = (
                "Medium"
                if source == "required"
                else "Low"
            )

            partial_skills.append(
                {
                    "skill": requirement,
                    "priority": priority,
                    "reason": (
                        "Related evidence is present in the "
                        "resume, but the exact requirement "
                        "is not explicitly demonstrated."
                    ),
                }
            )

            priority_gaps.append(
                {
                    "skill": requirement,
                    "priority": priority,
                    "reason": (
                        "Related experience exists, but "
                        "additional preparation is needed "
                        "for the exact requirement."
                    ),
                }
            )

            return

        # ---------------------------------------------
        # Missing
        # ---------------------------------------------

        priority = (
            "High"
            if source == "required"
            else "Medium"
        )

        missing_skills.append(
            {
                "skill": requirement,
                "priority": priority,
                "reason": (
                    "The exact requirement is not "
                    "explicitly demonstrated in the resume."
                ),
            }
        )

        priority_gaps.append(
            {
                "skill": requirement,
                "priority": priority,
                "reason": (
                    "The requirement is not explicitly "
                    "demonstrated in the resume."
                ),
            }
        )

    # -----------------------------------------------------
    # Process REQUIRED skills
    # -----------------------------------------------------

    for skill in required_skills:
        process_requirement(
            skill,
            "required",
        )

    # -----------------------------------------------------
    # Process PREFERRED skills
    # -----------------------------------------------------

    for skill in preferred_skills:
        process_requirement(
            skill,
            "preferred",
        )

    # -----------------------------------------------------
    # Explanation
    # -----------------------------------------------------

    demonstrated_count = (
        len(processed)
        - len(missing_skills)
        - len(partial_skills)
    )

    explanation = (
        f"The analysis evaluated {len(processed)} unique "
        f"job-related skills. "
        f"{demonstrated_count} are supported by explicit "
        f"resume evidence, {len(partial_skills)} have "
        f"related but incomplete evidence, and "
        f"{len(missing_skills)} are not explicitly "
        f"demonstrated."
    )

    result = SkillGapAnalysis(
        missing_skills=missing_skills,
        partial_skills=partial_skills,
        priority_gaps=priority_gaps,
        explanation=explanation,
    )

    return {
        "skill_gap_analysis": result.model_dump()
    }