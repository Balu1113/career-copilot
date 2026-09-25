import re

from agents.schemas import JobRequirements
from agents.services.skill_matching import (
    ALIASES,
    canonicalize,
    text_contains_alias,
)
from agents.services.structured_llm import generate_structured_output


# Stable display names for known canonical groups.
# Distinct technologies stay distinct (e.g. Azure Functions ≠ Microsoft Azure).
STABLE_DISPLAY_NAMES = {
    "llm": "LLMs",
    "apis": "APIs",
    "sdks": "SDKs",
    "ci cd": "Continuous integration",
    "react": "ReactJS",
    "microsoft azure": "Microsoft Azure",
    "azure functions": "Azure Functions",
    "azure ai search": "Azure AI Search",
    "cosmos db": "Cosmos DB",
    "mongodb": "MongoDB",
    "generative ai": "Generative AI",
    "machine learning": "Machine Learning",
    "microservices": "Microservices",
    "devops": "DevOps",
    "fastapi": "FastAPI",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "python": "Python",
    "rag": "RAG",
    "ai": "AI",
    "django rest framework": "Django REST Framework",
    "django": "Django",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "redis": "Redis",
    "next.js": "Next.js",
    "tailwind css": "Tailwind CSS",
    "spring boot": "Spring Boot",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "graphql": "GraphQL",
    "aws": "AWS",
    "github": "GitHub",
    "git": "Git",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "kafka": "Kafka",
    "apache spark": "Apache Spark",
    "spark": "Apache Spark",
    "pyspark": "PySpark",
    "databricks": "Databricks",
    "hadoop": "Hadoop",
    "hive": "Hive",
    "airflow": "Airflow",
    "snowflake": "Snowflake",
    "dbt": "dbt",
    "jest": "Jest",
    "vector databases": "Vector databases",
    "vector search": "Vector search",
    "prompt engineering": "Prompt Engineering",
    "ai agents": "AI Agents",
}


# Deterministic requirement_type lookup keyed by canonical_group.
#
# "technology"   — a named product, language, framework, cloud service, or tool
# "architecture" — an architectural pattern or structural approach
# "capability"   — a cross-cutting skill or practice with no single canonical product
#
# Everything not listed here defaults to "technology".
REQUIREMENT_TYPES: dict[str, str] = {
    # ---------- capabilities ----------
    "vector databases": "capability",
    "vector search": "capability",
    "rag": "capability",
    "prompt engineering": "capability",
    "ai agents": "capability",
    "agentic ai": "capability",
    "embeddings": "capability",
    "generative ai": "capability",
    "machine learning": "capability",
    "ai": "capability",
    "ci cd": "capability",
    "devops": "capability",
    "sdks": "capability",
    "apis": "capability",
    "llm": "capability",
    # ---------- architectures ----------
    "microservices": "architecture",
    # Everything else is "technology" by default.
}


# Supplemental tech vocabulary for deterministic recovery when the LLM
# misses an explicitly named technology. Not JD-specific — any JD that
# names these terms can recover them. Prefer longest aliases first via
# the scanner so "Azure AI Search" wins over bare "Azure"/"AI".
SUPPLEMENTAL_TECH_PATTERNS = [
    ("Azure AI Search", ["Azure AI Search", "Azure Cognitive Search", "Azure Search"]),
    ("Azure Functions", ["Azure Functions", "Azure Function"]),
    ("Cosmos DB", ["Azure Cosmos DB", "Cosmos DB", "CosmosDB", "Cosmos Database"]),
    ("MongoDB", ["MongoDB", "Mongo DB"]),
    ("Microsoft Azure", [
        "Microsoft Azure",
        "Azure Cloud Services",
        "Azure Cloud",
        "Azure Services",
        "Azure Platform",
        "Microsoft Azure Cloud",
        "Azure",
    ]),
    ("Continuous integration", [
        "Continuous Integration",
        "Continuous Delivery",
        "Continuous Deployment",
        "CI/CD",
        "CI CD",
        "CICD",
    ]),
    ("DevOps", ["DevOps", "Dev Ops"]),
    ("APIs", ["RESTful APIs", "REST APIs", "REST API", "APIs", "API"]),
    ("SDKs", ["Software Development Kits", "Software Development Kit", "SDKs", "SDK"]),
    ("Microservices", ["Microservices", "Microservice"]),
    ("FastAPI", ["FastAPI", "Fast API"]),
    ("ReactJS", ["ReactJS", "React.js", "React JS", "React"]),
    ("TypeScript", ["TypeScript", "Type Script"]),
    ("JavaScript", ["JavaScript", "Java Script"]),
    ("Python", ["Python"]),
    ("Java", ["Java"]),
    ("SQL", ["SQL"]),
    ("LLMs", ["Large Language Models", "Large Language Model", "LLMs", "LLM"]),
    ("RAG", [
        "Retrieval-Augmented Generation",
        "Retrieval Augmented Generation",
        "RAG",
    ]),
    ("Generative AI", [
        "Generative AI",
        "Generative Artificial Intelligence",
        "GenAI",
    ]),
    ("Machine Learning", ["Machine Learning"]),
    ("AI", ["AI"]),
    ("Django REST Framework", ["Django REST Framework", "DRF"]),
    ("Django", ["Django"]),
    ("PostgreSQL", ["PostgreSQL"]),
    ("MySQL", ["MySQL"]),
    ("Redis", ["Redis"]),
    ("Kafka", ["Kafka"]),
    ("Kubernetes", ["Kubernetes"]),
    ("Docker", ["Docker"]),
    ("Terraform", ["Terraform"]),
    ("PyTorch", ["PyTorch"]),
    ("TensorFlow", ["TensorFlow"]),
    ("Spring Boot", ["Spring Boot"]),
    ("GraphQL", ["GraphQL"]),
    ("Next.js", ["Next.js", "Next JS"]),
    ("Jest", ["Jest"]),
    ("Tailwind CSS", ["Tailwind CSS"]),
    ("AWS", ["Amazon Web Services", "AWS"]),
    ("Spark", ["Spark"]),
    ("Airflow", ["Airflow"]),
    ("Snowflake", ["Snowflake"]),
    ("dbt", ["dbt"]),
    ("Git", ["Git"]),
    ("GitHub", ["GitHub"]),
]


def _normalize_text(value):
    if not isinstance(value, str):
        return ""

    return " ".join(value.lower().split())


def _requirement_canonical(value):
    canonical = canonicalize(value) or _normalize_text(value)

    # Keep API/SDK plural forms consistent across the pipeline.
    if canonical == "sdk":
        return "sdks"
    if canonical == "api":
        return "apis"

    return canonical


def _build_scan_patterns():
    """
    Build (display_name, variants) pairs from shared ALIASES plus
    supplemental vocabulary. Longer variants are preferred by the scanner.
    """
    patterns = []
    seen_canonicals = set()

    for display_name, variants in SUPPLEMENTAL_TECH_PATTERNS:
        canonical = _requirement_canonical(display_name)
        seen_canonicals.add(canonical)
        patterns.append((display_name, list(variants)))

    for canonical, aliases in ALIASES.items():
        if canonical in seen_canonicals:
            continue

        display_name = STABLE_DISPLAY_NAMES.get(
            canonical,
            canonical.title(),
        )
        patterns.append((display_name, sorted(aliases, key=len, reverse=True)))
        seen_canonicals.add(canonical)

    return patterns


TECHNICAL_REQUIREMENT_PATTERNS = _build_scan_patterns()


def _technical_term_matches(text):
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return []

    candidates = []

    for display_name, variants in TECHNICAL_REQUIREMENT_PATTERNS:
        for variant in variants:
            normalized_variant = _normalize_text(variant)
            if not normalized_variant:
                continue

            pattern = rf"(?<!\w){re.escape(normalized_variant)}(?!\w)"
            for match in re.finditer(pattern, normalized_text):
                candidates.append(
                    {
                        "display_name": display_name,
                        "matched_text": normalized_text[
                            match.start():match.end()
                        ],
                        "start": match.start(),
                        "end": match.end(),
                        "length": len(normalized_variant),
                    },
                )

    candidates.sort(
        key=lambda item: (
            -item["length"],
            item["start"],
        ),
    )

    selected = []
    selected_canonicals = set()

    for candidate in candidates:
        canonical = _requirement_canonical(candidate["display_name"])
        overlaps = any(
            candidate["start"] < existing["end"]
            and existing["start"] < candidate["end"]
            for existing in selected
        )

        if overlaps or canonical in selected_canonicals:
            continue

        selected.append(candidate)
        selected_canonicals.add(canonical)

    selected.sort(key=lambda item: item["start"])
    return selected


def _format_matched_requirement(match):
    """Preserve the JD's wording when possible; fall back to display_name."""
    matched = _normalize_text(match.get("matched_text"))
    display_names = {
        "api": "API",
        "apis": "APIs",
        "sdk": "SDK",
        "sdks": "SDKs",
        "react": "ReactJS",
        "reactjs": "ReactJS",
        "react.js": "ReactJS",
        "react js": "ReactJS",
        "llm": "LLM",
        "llms": "LLMs",
        "rag": "RAG",
        "ai": "AI",
        "ml": "ML",
        "ci/cd": "CI/CD",
        "ci cd": "CI/CD",
        "cicd": "CI/CD",
        "azure": "Azure",
        "azure cloud": "Azure Cloud",
        "azure cloud services": "Azure Cloud Services",
        "microsoft azure": "Microsoft Azure",
        "azure ai search": "Azure AI Search",
        "azure functions": "Azure Functions",
        "cosmos db": "Cosmos DB",
        "fastapi": "FastAPI",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "django rest framework": "Django REST Framework",
        "next.js": "Next.js",
        "next js": "Next.js",
        "tailwind css": "Tailwind CSS",
        "amazon web services": "AWS",
        "aws": "AWS",
        "dbt": "dbt",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "redis": "Redis",
        "github": "GitHub",
        "genai": "GenAI",
        "continuous integration": "Continuous integration",
        "continuous delivery": "Continuous integration",
        "continuous deployment": "Continuous integration",
    }

    if matched in display_names:
        return display_names[matched]

    return match.get("display_name") or matched


def _section_source_for_match(normalized_text, start, end):
    """
    Classify a JD text match by the nearest preceding section heading.
    Returns required / preferred / job_description.
    """
    section_heads = [
        ("required skills", "required"),
        ("preferred skills", "preferred"),
        ("responsibilities", "responsibility"),
        ("experience requirements", "job_description"),
        ("education requirements", "job_description"),
        ("qualifications", "job_description"),
    ]

    best_heading = -1
    best_source = "job_description"

    for heading, source in section_heads:
        heading_pos = normalized_text.rfind(heading, 0, start)
        if heading_pos > best_heading:
            best_heading = heading_pos
            best_source = source

    if best_heading < 0:
        return "job_description"

    # Ensure the match is still inside this section (before the next heading).
    next_positions = [
        normalized_text.find(heading, best_heading + 1)
        for heading, _ in section_heads
    ]
    next_positions = [pos for pos in next_positions if pos > best_heading]

    if next_positions and end >= min(next_positions):
        return "job_description"

    return best_source


def _effective_registry_source(sources):
    for source in [
        "required",
        "preferred",
        "responsibility",
        "job_description",
    ]:
        if source in sources:
            return source

    return "required"


def _requirement_type_for(canonical_group: str) -> str:
    """Return the requirement_type for a canonical_group.

    Falls back to 'technology' for any group not in the lookup table.
    """
    return REQUIREMENT_TYPES.get(canonical_group, "technology")


def _add_registry_entry(registry, display_name, source):
    if not isinstance(display_name, str):
        return

    display_name = display_name.strip()
    if not display_name:
        return

    canonical_group = _requirement_canonical(display_name)
    if not canonical_group:
        return

    normalized_source = (
        source
        if source in {
            "required",
            "preferred",
            "responsibility",
            "job_description",
        }
        else "required"
    )

    for entry in registry:
        if entry["canonical_group"] != canonical_group:
            continue

        if display_name not in entry["original_names"]:
            entry["original_names"].append(display_name)

        if normalized_source not in entry["sources"]:
            entry["sources"].append(normalized_source)

        entry["source"] = _effective_registry_source(entry["sources"])
        return

    registry.append(
        {
            "display_name": display_name,
            "canonical_group": canonical_group,
            "requirement_type": _requirement_type_for(canonical_group),
            "source": normalized_source,
            "sources": [normalized_source],
            "original_names": [display_name],
        },
    )


def _add_registry_items(
    registry,
    items,
    default_source,
    job_description=None,
):
    if not isinstance(items, list):
        return

    for item in items:
        if isinstance(item, str):
            display_name = item
        elif isinstance(item, dict):
            display_name = item.get("display_name") or item.get("skill")
        else:
            continue

        if (
            job_description is not None
            and not _skill_is_explicitly_supported(
                display_name,
                job_description,
            )
        ):
            continue

        if isinstance(item, str):
            _add_registry_entry(
                registry,
                display_name,
                default_source,
            )
            continue

        sources = item.get("sources")
        if not isinstance(sources, list):
            sources = [item.get("source") or default_source]

        for source in sources:
            _add_registry_entry(
                registry,
                display_name,
                source,
            )


def _skill_is_explicitly_supported(skill, job_description):
    skill_text = _normalize_text(skill)
    job_text = _normalize_text(job_description)

    if not skill_text:
        return False

    if skill_text in job_text:
        return True

    if text_contains_alias(job_description, skill):
        return True

    # Alias-aware check via shared canonicalize vocabulary.
    canonical = _requirement_canonical(skill)
    if canonical and text_contains_alias(job_description, canonical):
        return True

    return False


def _filter_skills_against_job_description(skills, job_description):
    if not isinstance(skills, list):
        return []

    filtered = []

    for skill in skills:
        if not isinstance(skill, str):
            continue

        skill = skill.strip()
        if not skill:
            continue

        if not _skill_is_explicitly_supported(skill, job_description):
            continue

        if skill not in filtered:
            filtered.append(skill)

    return filtered


def _scan_job_description_into_registry(
    registry,
    job_description,
    responsibilities,
):
    """
    Deterministically recover explicitly named technologies from the JD
    and responsibilities. Classification uses section context when possible.
    """
    responsibility_texts = (
        [
            responsibility
            for responsibility in responsibilities
            if isinstance(responsibility, str)
        ]
        if isinstance(responsibilities, list)
        else []
    )

    for responsibility in responsibility_texts:
        for match in _technical_term_matches(responsibility):
            _add_registry_entry(
                registry,
                _format_matched_requirement(match),
                "responsibility",
            )

    normalized_jd = _normalize_text(job_description)
    for match in _technical_term_matches(job_description):
        source = _section_source_for_match(
            normalized_jd,
            match["start"],
            match["end"],
        )
        _add_registry_entry(
            registry,
            _format_matched_requirement(match),
            source,
        )


def _finalize_registry_entry(entry):
    canonical = entry["canonical_group"]
    stable = STABLE_DISPLAY_NAMES.get(canonical)
    if stable:
        entry["display_name"] = stable
    elif entry.get("original_names"):
        entry["display_name"] = entry["original_names"][0]

    entry["source"] = _effective_registry_source(entry.get("sources", []))

    # Ensure requirement_type is always present (entries created before this
    # field was added, or injected via LLM, may not carry it yet).
    if not entry.get("requirement_type"):
        entry["requirement_type"] = _requirement_type_for(canonical)

    return entry


def _build_requirement_registry(job_description, result_data):
    """
    Authoritative requirement registry.

    Build order:
      1. LLM required_skills
      2. LLM preferred_skills
      3. LLM requirement_registry (JD-validated)
      4. Deterministic scan of responsibilities + full JD text

    Alias variants (LLM / LLMs, Azure / Azure Cloud, CI/CD /
    Continuous integration) collapse into one canonical_group.
    Distinct technologies (Azure vs Azure Functions vs Azure AI Search,
    APIs vs SDKs vs Microservices) remain separate.
    """
    registry = []

    _add_registry_items(
        registry,
        result_data.get("required_skills", []),
        "required",
    )
    _add_registry_items(
        registry,
        result_data.get("preferred_skills", []),
        "preferred",
    )
    _add_registry_items(
        registry,
        result_data.get("requirement_registry", []),
        "required",
        job_description,
    )

    _scan_job_description_into_registry(
        registry,
        job_description,
        result_data.get("responsibilities", []),
    )

    return [_finalize_registry_entry(entry) for entry in registry]


def _lists_from_registry(registry):
    """
    Derive required_skills / preferred_skills from the registry.

    One display name per canonical_group. Preferred-only entries go to
    preferred_skills; everything else (required / responsibility /
    job_description) goes to required_skills.
    """
    required_skills = []
    preferred_skills = []
    seen = set()

    for entry in registry:
        canonical = entry.get("canonical_group")
        if not canonical or canonical in seen:
            continue

        seen.add(canonical)
        display_name = entry.get("display_name") or canonical

        if entry.get("source") == "preferred":
            preferred_skills.append(display_name)
        else:
            required_skills.append(display_name)

    return required_skills, preferred_skills


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

The authoritative artifact is requirement_registry. Downstream agents
consume required_skills and preferred_skills derived from that registry.

==================================================
1. REQUIRED SKILLS
==================================================

required_skills must contain only explicit technical skills, technologies,
programming languages, frameworks, databases, platforms, engineering tools,
or clearly named engineering practices that are presented as requirements.

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
2. RESPONSIBILITIES AND TECHNICAL REQUIREMENTS
==================================================

Keep activities, duties, operational tasks, and job responsibilities inside
the responsibilities field.

Do NOT automatically convert generic activities into required_skills:

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

However, an explicitly named technology, platform, language, framework,
database, API, SDK, cloud service, or engineering practice inside a
responsibility is a technical requirement. Include it in required_skills
and in requirement_registry when the responsibility requires using or
building it.

For example:

"Develop scalable APIs, SDKs, and microservices."

Extract all three technical requirements:

- APIs
- SDKs
- Microservices

Do not replace those requirements with the surrounding activity
"application development."

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
CI/CD -> Continuous integration
Azure Cloud / Azure cloud services / Azure -> Microsoft Azure

Do not convert a broad requirement into a more specific concept.

==================================================
12. REQUIREMENT REGISTRY (AUTHORITATIVE)
==================================================

Build requirement_registry from the entire job description FIRST.

Every unique technical requirement must appear once in the registry,
keyed by canonical_group:

1. Every explicit item in required_skills.
2. Every explicit item in preferred_skills.
3. Every explicit technical technology or engineering practice named
   inside responsibilities.
4. Every explicit technical technology or engineering practice named
   elsewhere in the job description.

Each registry item must be an object with:

- display_name: stable human-readable requirement wording
- canonical_group: lowercase normalized identity used only for grouping
- requirement_type: one of "technology", "architecture", or "capability" (see below)
- source: "required" or "preferred" (prefer required when both apply)
- sources: all sections where the requirement appears
- original_names: every wording variant seen in the JD

REQUIREMENT TYPE RULES:

"technology" — a named product, language, framework, cloud service, database,
  or tool with a single canonical identity.

  Examples:
    Python, FastAPI, MongoDB, Cosmos DB, Azure Functions, Azure AI Search,
    TypeScript, Redis, TensorFlow, Docker, Kubernetes, Git, GitHub

"architecture" — a structural or design pattern that describes HOW a system
  is organized, not a specific product.

  Examples:
    Microservices, Event-driven architecture, Serverless, REST

"capability" — a cross-cutting skill or practice that may be delivered through
  multiple different products. No single canonical tool satisfies it alone.

  Examples:
    Vector databases, RAG, Prompt Engineering, AI Agents, LLMs,
    CI/CD, DevOps, APIs, SDKs, Machine Learning, Generative AI

When in doubt between "technology" and "capability", use "technology" for
explicit product names and "capability" for practices or skill areas.

Alias variants MUST share one canonical_group. Examples:

- LLM, LLMs, Large Language Model -> one entry
- Continuous integration, CI/CD -> one entry
- Microsoft Azure, Azure Cloud, Azure cloud services, Azure -> one entry

Distinct technologies MUST remain separate. Examples:

- Microsoft Azure
- Azure Functions
- Azure AI Search
- Cosmos DB

are separate requirements.

APIs, SDKs, and Microservices are three distinct requirements.

Do not put generic activities such as collaboration, documentation,
debugging, testing, or monitoring into the registry unless the activity
itself is explicitly named as a technical engineering practice.

==================================================
13. NO DUPLICATES
==================================================

Do not duplicate equivalent skills across required_skills,
preferred_skills, or requirement_registry.

For example, do not return both:

"CI/CD"
"Continuous integration"

and do not return both:

"LLM"
"LLMs"

==================================================
14. STRICT OUTPUT FORMAT
==================================================

Return ONLY valid JSON matching the JobRequirements schema.

The output must contain exactly:

{
    "required_skills": [],
    "preferred_skills": [],
    "responsibilities": [],
    "experience_requirements": [],
    "education_requirements": [],
    "requirement_registry": []
}

List items must be plain strings. Registry items must be objects with the
exact fields described above.

No additional fields.
No markdown.
No explanations.

==================================================
15. FINAL VALIDATION
==================================================

Before returning the result, verify:

1. Every required skill is explicitly supported by the JD.
2. Every preferred skill is explicitly supported by the JD.
3. Every technical requirement found in responsibilities is represented
   in required_skills and requirement_registry.
4. Every explicit technology mentioned elsewhere in the JD is represented
   in requirement_registry.
5. Responsibilities have not been incorrectly converted into skills.
6. Generic testing activities remain responsibilities.
7. Generic monitoring activities remain responsibilities.
8. Troubleshooting and root-cause activities remain responsibilities.
9. No inferred technologies were added.
10. No invented education requirement exists.
11. Education is "Not specified" when absent from the JD.
12. No duplicate equivalent skills exist.
13. Distinct technologies remain separate in requirement_registry.
14. Alias variants share one canonical_group in requirement_registry.
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

Build requirement_registry as the authoritative normalized catalog of
every explicit technical requirement in the JD. Then populate
required_skills and preferred_skills consistently with that registry.

For REQUIRED SKILLS, focus on:

- programming languages
- frameworks
- databases
- cloud platforms
- APIs
- SDKs
- named engineering tools
- explicitly required engineering practices
- explicitly required technical technologies

For REQUIREMENT REGISTRY, scan the entire job description, including
responsibilities. Include every explicit technical requirement there, with
its original wording and whether it came from required skills, preferred
skills, or a responsibility.

Keep these DISTINCT unless the JD explicitly treats them as aliases:

- Microsoft Azure / Azure / Azure Cloud
- Azure Functions
- Azure AI Search
- Cosmos DB
- APIs
- SDKs
- Microservices

Merge these as ONE requirement each:

- LLM / LLMs / Large Language Model
- Continuous integration / CI/CD
- React / ReactJS / React.js

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

If the JD says:

"Develop scalable APIs, SDKs, and microservices for AI workflows."

Correct required skills include:

[
    "APIs",
    "SDKs",
    "Microservices"
]

If the JD says:

"Experience with source control and continuous integration."

Correct required skills:

[
    "Source control",
    "Continuous integration"
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

    result_data = result

    # ==================================================
    # FILTER LLM OUTPUT AGAINST THE JD
    # ==================================================

    result_data["required_skills"] = _filter_skills_against_job_description(
        result_data.get("required_skills", []),
        job_description,
    )

    result_data["preferred_skills"] = _filter_skills_against_job_description(
        result_data.get("preferred_skills", []),
        job_description,
    )

    # ==================================================
    # BUILD AUTHORITATIVE REQUIREMENT REGISTRY
    # ==================================================

    registry = _build_requirement_registry(
        job_description,
        result_data,
    )

    # ==================================================
    # DERIVE SKILL LISTS FROM THE REGISTRY
    # ==================================================

    required_skills, preferred_skills = _lists_from_registry(registry)

    result_data["requirement_registry"] = registry
    result_data["required_skills"] = required_skills
    result_data["preferred_skills"] = preferred_skills

    return {
        "job_requirements": result_data
    }
