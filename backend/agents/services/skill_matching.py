import re


# =========================================================
# NORMALIZATION
# =========================================================

from agents.services.skill_normalizer import normalize_skill

def normalize(text: str) -> str:
    return normalize_skill(text)

# =========================================================
# CANONICAL ALIASES
# =========================================================

ALIASES = {

    # -----------------------------------------------------
    # Frontend / Languages
    # -----------------------------------------------------

    "react": {
        "react",
        "reactjs",
        "react js",
        "react.js",
    },

    "python": {
        "python",
    },

    "javascript": {
        "javascript",
        "js",
    },

    "typescript": {
        "typescript",
        "type script",
        "ts",
    },

    # -----------------------------------------------------
    # AI / LLM
    # -----------------------------------------------------

    "llm": {
        "llm",
        "llms",
        "large language model",
        "large language models",
        "llm applications",
        "llm application",
    },

    "generative ai": {
        "generative ai",
        "genai",
        "generative artificial intelligence",
    },

    "rag": {
        "rag",
        "rag pipeline",
        "rag pipelines",
        "rag system",
        "rag systems",
        "retrieval augmented generation",
        "retrieval augmented generation pipeline",
        "retrieval augmented generation pipelines",
        "retrieval augmented generation system",
        "retrieval augmented generation systems",
        "retrieval-augmented generation",
        "retrieval-augmented generation pipeline",
        "retrieval-augmented generation pipelines",
        "retrieval-augmented generation system",
        "retrieval-augmented generation systems",
    },

    "ai agents": {
        "ai agent",
        "ai agents",
        "agentic ai",
        "agentic agents",
        "autonomous agents",
    },

    "prompt engineering": {
        "prompt engineering",
        "prompt engineering techniques",
    },

    "machine learning": {
        "machine learning",
        "ml",
    },

    "apis": {
        "api",
        "apis",
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "rest api development",
        "restful api development",
    },

    # -----------------------------------------------------
    # Backend
    # -----------------------------------------------------

    "fastapi": {
        "fastapi",
        "fast api",
    },

    "django": {
        "django",
    },

    "django rest framework": {
        "django rest framework",
        "drf",
    },

    # -----------------------------------------------------
    # Vector / Search
    # -----------------------------------------------------

    "vector databases": {
        "vector database",
        "vector databases",
        "vector db",
        "vector dbs",
    },

    "vector search": {
        "vector search",
        "vector searching",
    },

    "faiss": {
        "faiss",
    },

    # -----------------------------------------------------
    # Azure
    #
    # IMPORTANT:
    # All general Azure platform terminology maps to
    # "microsoft azure".
    #
    # Azure Functions and Azure AI Search remain separate
    # specialized skills.
    # -----------------------------------------------------

    "microsoft azure": {
        "microsoft azure",
        "azure",
        "azure cloud",
        "azure cloud services",
        "azure services",
        "azure platform",
        "microsoft azure cloud",
    },

    "azure functions": {
        "azure functions",
        "azure function",
    },

    "azure ai search": {
        "azure ai search",
        "azure cognitive search",
        "azure search",
    },

    # -----------------------------------------------------
    # Databases
    # -----------------------------------------------------

    "mongodb": {
        "mongodb",
        "mongo db",
        "mongo",
    },

    "cosmos db": {
        "cosmos db",
        "azure cosmos db",
        "cosmosdb",
        "cosmos database",
    },

    # -----------------------------------------------------
    # DevOps
    # -----------------------------------------------------

    "devops": {
        "devops",
        "dev ops",
    },

    "ci cd": {
        "ci",
        "ci cd",
        "cicd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
        "continuous integration and deployment",
        "ci/cd",
    },

    "deployment automation workflows": {
        "deployment automation",
        "deployment automation workflows",
        "deployment automation workflow",
        "automated deployment",
        "automated deployments",
    },

    # -----------------------------------------------------
    # Healthcare
    # -----------------------------------------------------

    "healthcare data systems": {
        "healthcare data systems",
        "health care data systems",
        "healthcare data",
        "health care data",
    },

    "healthcare workflow automation": {
        "healthcare workflow automation",
        "health care workflow automation",
    },

    "healthcare analytics": {
        "healthcare analytics",
        "health care analytics",
    },

    "nlp driven insights": {
        "nlp driven insights",
        "natural language processing insights",
        "nlp driven analytics",
        "nlp analytics",
    },

    # -----------------------------------------------------
    # AI / Platform
    # -----------------------------------------------------

    "ai optimization techniques": {
        "ai optimization techniques",
        "ai optimization",
        "llm optimization",
        "model optimization",
    },

    "model as a service": {
        "model as a service",
        "maas",
        "maas components",
        "model as a service components",
    },

    "automation": {
        "automation",
        "workflow automation",
    },
}


# =========================================================
# CANONICALIZATION
# =========================================================

NORMALIZED_ALIASES = {
    canonical: {
        normalize(alias)
        for alias in aliases
    }
    for canonical, aliases in ALIASES.items()
}


def canonicalize(text: str) -> str:
    normalized = normalize(text)

    for canonical, aliases in NORMALIZED_ALIASES.items():

        if normalized in aliases:
            return canonical

    return normalized


# =========================================================
# EXPLICIT TEXT EVIDENCE
# =========================================================

def text_contains_alias(
    text: str,
    canonical_skill: str,
) -> bool:

    if not text:
        return False

    normalized_text = normalize(text)

    aliases = NORMALIZED_ALIASES.get(
        canonical_skill,
        {normalize(canonical_skill)},
    )

    for alias in aliases:

        if not alias:
            continue

        pattern = rf"\b{re.escape(alias)}\b"

        if re.search(pattern, normalized_text):
            return True

    return False


# =========================================================
# CANDIDATE EVIDENCE
# =========================================================

def build_candidate_evidence(
    resume_intelligence: dict,
) -> set[str]:

    evidence = set()

    # -----------------------------------------------------
    # Structured fields
    # -----------------------------------------------------

    def add_structured(value):

        if not value:
            return

        if isinstance(value, str):

            canonical = canonicalize(value)

            if canonical:
                evidence.add(canonical)

        elif isinstance(value, list):

            for item in value:
                add_structured(item)

    add_structured(
        resume_intelligence.get(
            "skills",
            [],
        )
    )

    add_structured(
        resume_intelligence.get(
            "programming_languages",
            [],
        )
    )

    add_structured(
        resume_intelligence.get(
            "frameworks",
            [],
        )
    )

    add_structured(
        resume_intelligence.get(
            "tools_and_technologies",
            [],
        )
    )

    add_structured(
        resume_intelligence.get(
            "ai_ml_technologies",
            [],
        )
    )

    # -----------------------------------------------------
    # Projects
    # -----------------------------------------------------

    for project in resume_intelligence.get(
        "projects",
        [],
    ):

        if not isinstance(project, dict):
            continue

        add_structured(
            project.get(
                "technologies",
                [],
            )
        )

        for description in project.get(
            "description",
            [],
        ):

            add_structured(description)

    # -----------------------------------------------------
    # Professional experience
    # -----------------------------------------------------

    for experience in resume_intelligence.get(
        "experience",
        [],
    ):

        if not isinstance(experience, dict):
            continue

        add_structured(
            experience.get(
                "technologies",
                [],
            )
        )

        for description in experience.get(
            "description",
            [],
        ):

            add_structured(description)

    return evidence


# =========================================================
# BUILD FULL RESUME TEXT
# =========================================================

def build_resume_evidence_text(
    resume_intelligence: dict,
) -> str:

    parts = []

    # -----------------------------------------------------
    # Professional Summary
    # -----------------------------------------------------

    summary = resume_intelligence.get(
        "professional_summary",
        "",
    )

    if summary:
        parts.append(summary)

    # -----------------------------------------------------
    # Structured fields
    # -----------------------------------------------------

    for field in [
        "skills",
        "programming_languages",
        "frameworks",
        "tools_and_technologies",
        "ai_ml_technologies",
    ]:

        values = resume_intelligence.get(
            field,
            [],
        )

        if values:

            parts.extend(
                str(value)
                for value in values
            )

    # -----------------------------------------------------
    # Projects
    # -----------------------------------------------------

    for project in resume_intelligence.get(
        "projects",
        [],
    ):

        if not isinstance(project, dict):
            continue

        parts.append(
            str(
                project.get(
                    "name",
                    "",
                )
            )
        )

        parts.extend(
            str(value)
            for value in project.get(
                "description",
                [],
            )
        )

        parts.extend(
            str(value)
            for value in project.get(
                "technologies",
                [],
            )
        )

    # -----------------------------------------------------
    # Experience
    # -----------------------------------------------------

    for experience in resume_intelligence.get(
        "experience",
        [],
    ):

        if not isinstance(experience, dict):
            continue

        parts.append(
            str(
                experience.get(
                    "company",
                    "",
                )
            )
        )

        parts.append(
            str(
                experience.get(
                    "role",
                    "",
                )
            )
        )

        parts.extend(
            str(value)
            for value in experience.get(
                "description",
                [],
            )
        )

        parts.extend(
            str(value)
            for value in experience.get(
                "technologies",
                [],
            )
        )

    return " ".join(parts)


# =========================================================
# DIRECT EVIDENCE
# =========================================================

def has_direct_evidence(
    requirement: str,
    candidate_evidence: set[str],
    resume_text: str = "",
) -> bool:

    requirement_canonical = canonicalize(
        requirement
    )

    # -----------------------------------------------------
    # Structured evidence
    # -----------------------------------------------------

    if requirement_canonical in candidate_evidence:
        return True

    # -----------------------------------------------------
    # Full resume text
    # -----------------------------------------------------

    if resume_text:

        if text_contains_alias(
            resume_text,
            requirement_canonical,
        ):
            return True

    return False


# =========================================================
# PARTIAL RELATIONSHIPS
# =========================================================

PARTIAL_RELATIONSHIPS = {

    # -----------------------------------------------------
    # Backend
    # -----------------------------------------------------

    # Python/Django does NOT demonstrate FastAPI.
    "fastapi": set(),

    # -----------------------------------------------------
    # Vector / Search
    # -----------------------------------------------------

    # RAG/vector search/FAISS provide related evidence,
    # but do not prove experience with a vector database.
    "vector databases": {
        "rag",
        "vector search",
        "faiss",
    },

    # RAG/vector search/vector databases provide related
    # evidence for Azure AI Search, but do not demonstrate
    # Azure-specific experience.
    "azure ai search": {
        "rag",
        "vector databases",
        "vector search",
        "faiss",
    },

    # -----------------------------------------------------
    # Azure
    # -----------------------------------------------------

    # Knowing Azure in general does NOT demonstrate:
    # Azure Functions or Azure AI Search.
    "microsoft azure": set(),

    "azure cloud services": set(),

    "azure functions": set(),

    # -----------------------------------------------------
    # Databases
    # -----------------------------------------------------

    # Vector database experience can be related to MongoDB,
    # but does not prove MongoDB experience.
    "mongodb": {
        "vector databases",
    },

    # Same principle for Cosmos DB.
    "cosmos db": {
        "vector databases",
    },

    # -----------------------------------------------------
    # Healthcare
    # -----------------------------------------------------

    "healthcare data systems": set(),

    "healthcare workflow automation": {
        "automation",
    },

    "healthcare analytics": set(),

    "nlp driven insights": set(),

    # -----------------------------------------------------
    # AI optimization
    # -----------------------------------------------------

    "ai optimization techniques": set(),

    # -----------------------------------------------------
    # DevOps
    # -----------------------------------------------------

    "devops": set(),

    "ci cd": set(),

    "deployment automation workflows": set(),

    # -----------------------------------------------------
    # Model as a Service
    # -----------------------------------------------------

    "model as a service": set(),
}


def has_partial_evidence(
    requirement: str,
    candidate_evidence: set[str],
    resume_text: str = "",
) -> bool:

    requirement_canonical = canonicalize(
        requirement
    )

    related_skills = PARTIAL_RELATIONSHIPS.get(
        requirement_canonical,
        set(),
    )

    if not related_skills:
        return False

    # -----------------------------------------------------
    # Structured evidence
    # -----------------------------------------------------

    if set(related_skills).intersection(
        candidate_evidence
    ):
        return True

    # -----------------------------------------------------
    # Full resume text
    # -----------------------------------------------------

    for related_skill in related_skills:

        if text_contains_alias(
            resume_text,
            related_skill,
        ):
            return True

    return False


# =========================================================
# CLASSIFICATION
# =========================================================

def classify_requirement(
    requirement: str,
    candidate_evidence: set[str],
    confirmed_matches: set[str] | None = None,
    resume_text: str = "",
) -> str:

    # IMPORTANT:
    #
    # Resume Intelligence is the source of truth.
    #
    # Resume Analysis / confirmed_matches must NOT override
    # deterministic evidence matching.
    #
    # This prevents an LLM from claiming that a skill exists
    # when it is not explicitly supported by the resume.

    # -----------------------------------------------------
    # Explicit resume evidence
    # -----------------------------------------------------

    if has_direct_evidence(
        requirement,
        candidate_evidence,
        resume_text,
    ):
        return "demonstrated"

    # -----------------------------------------------------
    # Related but incomplete evidence
    # -----------------------------------------------------

    if has_partial_evidence(
        requirement,
        candidate_evidence,
        resume_text,
    ):
        return "partial"

    # -----------------------------------------------------
    # No evidence
    # -----------------------------------------------------

    return "missing"