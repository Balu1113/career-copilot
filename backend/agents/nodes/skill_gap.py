import re
from typing import Literal

from pydantic import BaseModel

from agents.schemas import SkillGapAnalysis
from agents.services.structured_llm import (
    generate_structured_output,
)
from agents.services.skill_matching import (
    canonicalize,
)


def _iter_requirement_entries(job_requirements):
    if not isinstance(job_requirements, dict):
        return []

    registry = job_requirements.get("requirement_registry", [])
    entries = []
    seen = set()

    if isinstance(registry, list):
        for item in registry:
            if not isinstance(item, dict):
                continue

            display_name = item.get("display_name") or item.get("skill")
            if not isinstance(display_name, str):
                continue

            display_name = display_name.strip()
            if not display_name:
                continue

            sources = item.get("sources")
            if not isinstance(sources, list):
                source = item.get("source") or "required"
                sources = [source]

            source = (
                "required"
                if "required" in sources
                else (
                    "preferred"
                    if "preferred" in sources
                    else "required"
                )
            )

            canonical = item.get("canonical_group") or canonicalize(display_name)

            if canonical and canonical in seen:
                continue

            if canonical:
                seen.add(canonical)

            entries.append((display_name, source))

        if entries:
            return entries

    required_skills = job_requirements.get("required_skills", [])
    preferred_skills = job_requirements.get("preferred_skills", [])

    if not isinstance(required_skills, list):
        required_skills = []

    if not isinstance(preferred_skills, list):
        preferred_skills = []

    return [
        (skill, "required")
        for skill in required_skills
        if isinstance(skill, str)
    ] + [
        (skill, "preferred")
        for skill in preferred_skills
        if isinstance(skill, str)
    ]


def _is_confirmed_equivalent(
    requirement: str,
    confirmed_skill: str,
) -> bool:
    """Return whether two skills belong to the same canonical group."""

    requirement_key = canonicalize(requirement)
    confirmed_key = canonicalize(confirmed_skill)

    return bool(
        requirement_key
        and confirmed_key
        and requirement_key == confirmed_key
    )

class SemanticGapDecision(BaseModel):
    skill: str
    classification: Literal["partial", "missing"]
    evidence_basis: str


class SemanticGapClassification(BaseModel):
    decisions: list[SemanticGapDecision]



MISSING_EVIDENCE_BASIS = (
    "No meaningful transferable evidence was identified "
    "in the resume."
)


def _is_sdk_requirement(requirement: str) -> bool:
    if not isinstance(requirement, str):
        return False

    normalized = " ".join(requirement.lower().split())

    return bool(
        re.search(
            r"\b(?:sdk|software development kit)s?\b",
            normalized,
        )
        or "sdk development" in normalized
    )


def _evidence_shows_sdk_development(evidence_basis: str) -> bool:
    if not isinstance(evidence_basis, str):
        return False

    normalized = " ".join(evidence_basis.lower().split())

    return bool(
        re.search(
            r"\b(?:sdk|software development kit)s?\s+development\b",
            normalized,
        )
        or re.search(
            r"\b(?:developed|built|created|designed|implemented|authored)\b"
            r"[^.]{0,60}\b(?:an?\s+)?(?:sdk|software development kit)s?\b",
            normalized,
        )
    )


def _apply_conservative_policy(
    requirement: str,
    classification: str,
    evidence_basis: str,
) -> tuple[str, str]:
    if (
        _is_sdk_requirement(requirement)
        and classification == "partial"
        and not _evidence_shows_sdk_development(evidence_basis)
    ):
        return (
            "missing",
            "Resume evidence shows SDK or API consumption, "
            "not SDK development.",
        )

    return classification, evidence_basis


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
You are a CONSERVATIVE skill-gap classification engine.

Your task is to decide whether each job requirement that is NOT
explicitly demonstrated by the candidate has MEANINGFUL, technically
transferable evidence in the resume.

There are only two possible classifications:

- partial
- missing

IMPORTANT:

1. You are NOT allowed to classify anything as demonstrated.

2. PARTIAL means the resume proves meaningful capability that
   transfers DIRECTLY toward the requirement even though the
   exact technology is not named.

   Good examples:

   FastAPI  <-  Python + Django/Django REST Framework +
                REST API backend experience

   Vector databases  <-  The resume demonstrates embeddings, vector search, and
                RAG concepts, which provide related knowledge, but does not
                explicitly demonstrate operating a vector database.

3. MISSING means the resume provides no meaningful technical
   evidence that transfers toward the requirement.

   Evidence from a WIDER, ADJACENT or FAMILY-related area is NOT
   automatically transferable. The overlap must be direct and
   meaningful.

   Examples that must be MISSING:

   - MongoDB / Cosmos DB <- resume has PostgreSQL, MySQL or Redis.
     Generic database or relational experience does NOT transfer
     to a specific NoSQL/document store the candidate never used.
   - TypeScript <- resume has JavaScript. The resume demonstrates JavaScript
     and React, but does not explicitly demonstrate TypeScript.
   - Microservices <- resume has Django / Django REST Framework.
     The resume demonstrates backend applications built with Django and
     Django REST Framework, but does not explicitly demonstrate
     microservices architecture.
   - Microsoft Azure <- resume has cloud or web deployment to
     other platforms. General cloud knowledge is not Azure.
   - Azure Functions <- no Azure or serverless experience at all.
   - CI/CD <- resume has Git version control only. Git alone is
     not a continuous integration pipeline.
   - SDKs / SDK development <- resume uses APIs or third-party
     SDKs, but does not show building or developing an SDK.
   - FastAPI <- NOT satisfied by Django alone. Only mark partial
     when the resume shows direct REST API development experience
     that transfers.

4. Do not treat generic knowledge as transferable:
   - "database experience" does not prove a specific database.
   - "backend experience" does not prove serverless or Azure.
   - "JavaScript" does not prove "TypeScript".
   - "Git" does not prove "CI/CD" or "DevOps".
   - Docker does not prove Kubernetes.
   - Python backend experience does not prove AWS Lambda.
   - WebSockets does not prove Kafka.
   - DevOps experience does not prove Terraform.
   - TensorFlow does not prove PyTorch.
   - REST APIs does not prove GraphQL.

5. Provide evidence_basis for EVERY decision:
   - A short factual explanation grounded ONLY in the supplied
     resume text. Quote which resume evidence was used.
   - partial example for Vector databases: "The resume demonstrates embeddings, vector search, and RAG concepts, which provide related knowledge, but does not explicitly demonstrate operating a vector database."
   - partial example for FastAPI: "Python + Django REST Framework + REST API development provides transferable API framework knowledge."
   - missing example for TypeScript: "The resume demonstrates JavaScript and React, but does not explicitly demonstrate TypeScript."
   - missing example for Microservices: "The resume demonstrates backend applications built with Django and Django REST Framework, but does not explicitly demonstrate microservices architecture."
   - missing example for MongoDB: "Resume only shows PostgreSQL/MySQL/Redis; no MongoDB-specific evidence exists."

6. Do not invent resume experience.

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
- evidence_basis: a short factual sentence explaining which
  resume evidence supports the classification (quote the resume)

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

        basis = decision.evidence_basis

        if not isinstance(basis, str):
            basis = ""

        basis = " ".join(basis.strip().split())

        decisions[skill_key] = {
            "classification": decision.classification,
            "evidence_basis": (
                basis or MISSING_EVIDENCE_BASIS
            ),
        }

    # Backfill any requirements the LLM silently dropped so every
    # canonical key is guaranteed to exist in the decisions map.
    for requirement in requirements:
        key = canonicalize(requirement)
        if key and key not in decisions:
            print(
                f"[skill_gap] WARNING: LLM dropped decision "
                f"for '{requirement}' (canonical: '{key}'). "
                f"Defaulting to 'missing'."
            )
            decisions[key] = {
                "classification": "missing",
                "evidence_basis": MISSING_EVIDENCE_BASIS,
            }

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

    requirement_entries = _iter_requirement_entries(job_requirements)

    requirement_groups = {}

    for skill, source in requirement_entries:
        if not isinstance(skill, str):
            continue

        canonical = canonicalize(skill)
        if not canonical:
            continue

        group = requirement_groups.setdefault(
            canonical,
            {
                "canonical_group": canonical,
                "display_name": skill,
                "original_names": [],
                "sources": [],
            },
        )

        if skill not in group["original_names"]:
            group["original_names"].append(skill)

        if source not in group["sources"]:
            group["sources"].append(source)

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
    demonstrated_skills = []

    processed = set()

    # -----------------------------------------------------
    # First pass: identify all requirements that are demonstrated
    # -----------------------------------------------------

    for requirement, _source in requirement_entries:

        canonical_requirement = canonicalize(
            requirement
        )

        if not canonical_requirement:
            continue

        if canonical_requirement in processed:
            continue

        # Resume Analyzer already confirmed it.
        if any(
            _is_confirmed_equivalent(
                canonical_requirement,
                confirmed_skill,
            )
            for confirmed_skill in confirmed_matches
        ):
            processed.add(canonical_requirement)
            demonstrated_skills.append(canonical_requirement)

    # -----------------------------------------------------
    # Second pass: classify all remaining requirements
    # -----------------------------------------------------

    # Collect all requirements that are NOT yet demonstrated
    # Deduplicate by canonical form to avoid sending duplicates to LLM
    remaining_requirements = []
    remaining_seen = set()

    for requirement, _source in requirement_entries:

        canonical_requirement = canonicalize(
            requirement
        )

        if not canonical_requirement:
            continue

        if canonical_requirement in processed:
            continue

        if canonical_requirement in remaining_seen:
            continue

        remaining_seen.add(canonical_requirement)
        remaining_requirements.append(requirement)

    # Classify all remaining requirements through semantic analysis
    semantic_decisions = classify_semantic_gaps(
        requirements=remaining_requirements,
        resume_intelligence=resume_intelligence,
        resume_analysis=resume_analysis,
    )
    # -----------------------------------------------------

    # Helper
    # -----------------------------------------------------

    def build_skill_reason(
        classification,
        evidence_basis="",
    ):
        if classification == "partial":
            reason = (
                "Related evidence is present in the resume, "
                "but the exact requirement is not explicitly "
                "demonstrated."
            )
        else:
            reason = (
                "The exact requirement is not explicitly "
                "demonstrated in the resume."
            )

        basis = " ".join(
            evidence_basis.strip().split()
        ) if isinstance(evidence_basis, str) else ""

        if basis and basis != MISSING_EVIDENCE_BASIS:
            reason += f" Evidence basis: {basis}"

        return reason

    def build_gap_reason(classification):
        if classification == "partial":
            return (
                "Related experience exists, but "
                "additional preparation is needed "
                "for the exact requirement."
            )

        return (
            "The requirement is not explicitly "
            "demonstrated in the resume."
        )

    def resolve_decision(canonical_requirement):
        decision = semantic_decisions.get(
            canonical_requirement,
        )

        if isinstance(decision, str):
            classification = (
                decision
                if decision in {"partial", "missing"}
                else "missing"
            )
            return classification, MISSING_EVIDENCE_BASIS

        if not isinstance(decision, dict):
            decision = {}

        return decision.get(
            "classification",
            "missing",
        ), decision.get(
            "evidence_basis",
            "",
        )

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
            # Skill already processed, skip to avoid duplicates
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
        # Do NOT allow the semantic decisions to override it.
        # -------------------------------------------------

        if any(
            _is_confirmed_equivalent(
                canonical_requirement,
                confirmed_skill,
            )
            for confirmed_skill in confirmed_matches
        ):
            demonstrated_skills.append(canonical_requirement)
            return

        # -------------------------------------------------
        # For everything not explicitly confirmed by the
        # Resume Analyzer, use the semantic decisions.
        # -------------------------------------------------

        classification, evidence_basis = _apply_conservative_policy(
            requirement,
            *resolve_decision(canonical_requirement),
        )

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
                    "reason": build_skill_reason(
                        classification,
                        evidence_basis,
                    ),
                }
            )

            priority_gaps.append(
                {
                    "skill": requirement,
                    "priority": priority,
                    "reason": build_gap_reason(
                        classification
                    ),
                }
            )

            return

        # ---------------------------------------------
        # Missing (or any unexpected classification)
        # ---------------------------------------------

        classification = "missing"

        priority = (
            "High"
            if source == "required"
            else "Medium"
        )

        missing_skills.append(
            {
                "skill": requirement,
                "priority": priority,
                "reason": build_skill_reason(
                    classification,
                    evidence_basis,
                ),
            }
        )

        priority_gaps.append(
            {
                "skill": requirement,
                "priority": priority,
                "reason": build_gap_reason(
                    classification
                ),
            }
        )

    # -----------------------------------------------------
    # Process REQUIRED skills
    # -----------------------------------------------------

    for skill, source in requirement_entries:
        process_requirement(
            skill,
            source,
        )


    merged_requirements = []

    for group in requirement_groups.values():
        if len(group["original_names"]) <= 1:
            continue

        merged_requirements.append({
            "canonical_group": group["canonical_group"],
            "display_name": group["display_name"],
            "original_names": list(group["original_names"]),
            "source": (
                "required"
                if "required" in group["sources"]
                else "preferred"
            ),
            "sources": list(group["sources"]),
        })

    # -----------------------------------------------------
    # Explanation
    # -----------------------------------------------------

    demonstrated_count = len(demonstrated_skills)
    total_classified = (
        demonstrated_count
        + len(partial_skills)
        + len(missing_skills)
    )

    registry = job_requirements.get("requirement_registry", [])
    if isinstance(registry, list) and registry:
        preferred_count = sum(
            1
            for item in registry
            if isinstance(item, dict)
            and item.get("source") == "preferred"
        )
        required_count = sum(
            1
            for item in registry
            if isinstance(item, dict)
            and item.get("source") != "preferred"
        )
    else:
        required_count = len(required_skills)
        preferred_count = len(preferred_skills)

    listed_total = required_count + preferred_count

    merge_notes = []

    for group in merged_requirements:
        aliases = [
            name
            for name in group["original_names"]
            if name != group["display_name"]
        ]

        if not aliases:
            continue

        alias_text = ", ".join(f'"{name}"' for name in aliases)
        merge_notes.append(
            f"{alias_text} was grouped with "
            f'"{group["display_name"]}" '
            f'(canonical group: {group["canonical_group"]})'
        )

    merge_note = ""
    if merge_notes:
        merge_note = " Merged terminology: " + "; ".join(merge_notes) + "."

    explanation = (
        f"The job lists {listed_total} skills "
        f"({required_count} required, {preferred_count} preferred). "
        f"After merging equivalent terminology, "
        f"{total_classified} unique job-related skills were evaluated: "
        f"{demonstrated_count} are supported by explicit "
        f"resume evidence, {len(partial_skills)} have "
        f"related but incomplete evidence, and "
        f"{len(missing_skills)} are not explicitly "
        f"demonstrated."
        f"{merge_note}"
    )

    result = SkillGapAnalysis(
        missing_skills=missing_skills,
        partial_skills=partial_skills,
        priority_gaps=priority_gaps,
        explanation=explanation,
        merged_requirements=merged_requirements,
    )

    return {
        "skill_gap_analysis": result.model_dump()
    }
