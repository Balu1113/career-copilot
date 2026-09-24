from pydantic import BaseModel

from agents.services.structured_llm import (
    generate_structured_output,
)

from resume_builder.schemas import (
    GeneratedResumeContent,
    ResumeOptimization,
    ResumeSummaryOutput,
)


RESUME_OPTIMIZATION_SYSTEM_PROMPT = """
You are a professional ATS resume optimization assistant.

Your task is to optimize ONLY the SKILLS and PROJECTS
sections of a resume based on a target job description.

STRICT RULES:

1. Return ONLY the requested structured JSON.

2. SKILLS:
   - Identify the important skills and technologies
     requested by the job description.
   - Add the skills requested by the job description.
   - Keep existing skills that are relevant to the job.
   - Remove skills that are clearly unrelated to the job.
   - Organize skills into useful categories.
   - Do not remove important general skills such as
     Python, SQL, Git, REST APIs when they are relevant.
   - A JD-required skill may be included in the Skills
     section even if it was not present in the source resume.
   - Skills are NOT professional-experience claims.

3. PROJECTS:
   - Keep existing projects relevant to the JD.
   - Remove clearly unrelated projects.
   - You may create ONE additional project that is
     directly relevant to the JD.
   - A newly generated project must not be presented
     as employment experience.
   - Keep the generated project concise and technically
     relevant to the JD.

4. DO NOT modify:
   - name
   - email
   - phone
   - location
   - LinkedIn
   - GitHub
   - website
   - professional summary
   - work experience
   - job titles
   - companies
   - experience dates
   - experience bullets
   - education
   - certifications
   - publications

5. Do not rewrite or invent employment experience.

6. Do not add employers, job titles, employment dates,
   employment responsibilities or employment achievements.

7. Skills requested by the JD can be added to the
   Skills section without claiming that they were used
   professionally.

8. Return every required field.

9. Return empty arrays when there are no relevant projects.

10. Return ONLY valid JSON.
"""


RESUME_OPTIMIZATION_USER_PROMPT = """
Optimize the resume for the following job description.

JOB DESCRIPTION:
{job_description}

EXISTING RESUME:

SKILLS:
{skills}

PROJECTS:
{projects}

TASK:

1. Extract the important skills and technologies from
   the job description.

2. Add those JD-required skills to the Skills section.

3. Keep existing skills that are relevant.

4. Remove clearly unrelated skills.

5. Keep projects relevant to the JD.

6. Remove clearly unrelated projects.

7. If useful, create ONE additional project that
   demonstrates the technologies requested by the JD.

8. Do not modify or create professional employment
   experience.

Return ONLY:

{{
    "skills": {{
        "Category": ["skill1", "skill2"]
    }},
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [],
            "url": "",
            "bullets": []
        }}
    ]
}}
"""

RESUME_SUMMARY_SYSTEM_PROMPT = """
You are a professional resume writer.

Create a concise, ATS-friendly professional summary based only on the provided resume details.

Rules:
- Write 2 to 4 sentences.
- Highlight the candidate's core role, strengths, and relevant experience.
- Use only information present in the resume.
- Do not invent job titles, companies, metrics, or achievements.
- Keep the summary professional and polished.
- Return only valid JSON.
"""

RESUME_SUMMARY_USER_PROMPT = """
Generate a professional summary for the resume below.

JOB DESCRIPTION:
{job_description}

RESUME CONTENT:
{resume_content}

Return ONLY:
{{
  "summary": "..."
}}
"""


def generate_resume_summary(
    resume_content,
    job_description="",
):
    if resume_content is None:
        raise ValueError(
            "Resume content is required."
        )

    prompt = RESUME_SUMMARY_USER_PROMPT.format(
        job_description=(
            job_description.strip()
            if job_description
            else "No specific target role provided."
        ),
        resume_content=resume_content,
    )

    result = generate_structured_output(
        system_prompt=RESUME_SUMMARY_SYSTEM_PROMPT,
        user_prompt=prompt,
        schema=ResumeSummaryOutput,
    )

    summary = result.get("summary", "")
    return summary.strip()


def generate_resume_optimization(
    skills,
    projects,
    job_description,
):
    if not job_description.strip():
        raise ValueError(
            "Job description is required."
        )

    prompt = RESUME_OPTIMIZATION_USER_PROMPT.format(
        job_description=job_description,
        skills=skills,
        projects=projects,
    )

    return generate_structured_output(
        system_prompt=RESUME_OPTIMIZATION_SYSTEM_PROMPT,
        user_prompt=prompt,
        schema=ResumeOptimization,
    )


RESUME_MODIFY_SYSTEM_PROMPT = """
You are a professional resume editing AI agent.

You will receive the current resume content as JSON and a single user
instruction describing the change to make.

Rules:
- Return the COMPLETE updated resume as valid JSON matching the schema.
- Keep every section that is not affected by the instruction exactly the same.
- Do not invent employers, job titles, companies, dates, degrees, metrics,
  achievements, or experience that is not in the resume or explicitly provided
  in the user instruction.
- Wording improvements must stay truthful to the existing content.
- Keep the professional summary to 2-4 sentences.
- Return ONLY valid JSON.
"""


RESUME_MODIFY_USER_PROMPT = """
Apply the instruction below to the resume content.

INSTRUCTION:
{instruction}

JOB DESCRIPTION (optional context):
{job_description}

CURRENT RESUME CONTENT:
{resume_content}

Return ONLY the complete updated resume JSON object.
"""


def modify_resume_content(
    resume_content,
    instruction,
    job_description="",
):
    if resume_content is None:
        raise ValueError(
            "Resume content is required."
        )

    instruction = instruction.strip()

    if not instruction:
        raise ValueError(
            "Instruction is required."
        )

    prompt = RESUME_MODIFY_USER_PROMPT.format(
        instruction=instruction,
        job_description=(
            job_description.strip()
            if job_description
            else "No specific target role provided."
        ),
        resume_content=resume_content,
    )

    return generate_structured_output(
        system_prompt=RESUME_MODIFY_SYSTEM_PROMPT,
        user_prompt=prompt,
        schema=GeneratedResumeContent,
    )