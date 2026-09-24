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
        "autonomous agents",
    },

    "agentic ai": {
        "agentic ai",
        "agentic agents",
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
    },

    "rest apis": {
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
    # Architecture
    # -----------------------------------------------------

    "microservices": {
        "microservice",
        "microservices",
    },

    # -----------------------------------------------------
    # Big Data / Data Engineering
    # -----------------------------------------------------

    "apache spark": {
        "apache spark",
        "spark",
    },

    "pyspark": {
        "pyspark",
        "py spark",
    },

    "databricks": {
        "databricks",
        "data bricks",
        "data-bricks",
        "azure databricks",
    },

    "hadoop": {
        "hadoop",
        "apache hadoop",
    },

    "hive": {
        "hive",
        "apache hive",
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

    "version control": {
        "git",
        "version control",
        "source control",
        "source code management",
        "scm",
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
    if not isinstance(text, str):
        return ""

    normalized = normalize(text)
    if not normalized:
        return ""

    # 1. Direct ALIASES lookup
    for canonical, aliases in NORMALIZED_ALIASES.items():
        if normalized in aliases:
            return canonical

    # 2. Generic compact lookup (strips spaces, hyphens, dots, slashes)
    compact_normalized = re.sub(r"[^a-z0-9]", "", normalized)
    if compact_normalized:
        for canonical, aliases in NORMALIZED_ALIASES.items():
            for alias in aliases:
                if re.sub(r"[^a-z0-9]", "", alias) == compact_normalized:
                    return canonical

    # 3. Ecosystem vendor prefix removal (e.g. "apache spark" -> "spark")
    vendor_prefixes = ("apache ", "microsoft ", "amazon ", "google cloud ")
    for prefix in vendor_prefixes:
        if normalized.startswith(prefix):
            stripped = normalized[len(prefix):].strip()
            for canonical, aliases in NORMALIZED_ALIASES.items():
                if stripped in aliases:
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