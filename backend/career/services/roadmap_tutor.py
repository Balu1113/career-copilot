from agents.services.structured_llm import generate_structured_output
from career.schemas import RoadmapLessonPlan, RoadmapTutorLesson

LESSON_COLLECTIONS = {
    "skill": "skills_to_learn",
    "topic": "learning_topics",
    "project": "recommended_projects",
    "phase": "phases",
}

LEVELS = ["beginner", "intermediate", "advanced"]


def build_roadmap_inventory(roadmap):
    inventory = []

    for content_type, collection in LESSON_COLLECTIONS.items():
        items = roadmap.get(collection, []) or []

        for index, item in enumerate(items):
            inventory.append(
                {
                    "content_type": content_type,
                    "item_index": index,
                    "item": item,
                }
            )

    return inventory


def generate_roadmap_lesson_plan(*, roadmap, level):
    system_prompt = """
You are an experienced curriculum designer and career tutor.
You build ordered lesson plans from a career roadmap. You only
reorganize and describe the roadmap content given to you: never
invent extra skills, topics, projects, or phases.
""".strip()

    inventory = build_roadmap_inventory(roadmap)

    item_lines = [
        f"- type={entry['content_type']} "
        f"index={entry['item_index']}: {entry['item']}"
        for entry in inventory
    ]

    user_prompt = f"""
Build a complete, ordered lesson plan for the career roadmap below.
Create exactly one lesson for every roadmap item listed, keeping the
given order. Do not skip any item and do not add lessons for items
that are not listed.

TARGET ROLE:
{roadmap.get("target_role", "")}

ROADMAP SUMMARY:
{roadmap.get("summary", "")}

LEARNER STARTING LEVEL:
{level}
Pitch the first lessons at this level. Gradually raise each lesson's
level field to "intermediate" or "advanced" where the roadmap content
genuinely grows in difficulty, so the plan progresses from easier to
harder lessons. Use only these three level values:
{", ".join(LEVELS)}.

ROADMAP ITEMS (one lesson each, keep this order):
{chr(10).join(item_lines)}

For every item return:
- content_type and item_index copied exactly from the item list
- level: beginner, intermediate, or advanced
- a concise lesson title specific to the item
- a one or two sentence overview of what the lesson teaches
- a realistic estimated_time (for example "25 minutes")
""".strip()

    return generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=RoadmapLessonPlan,
        max_retries=2,
    )


def generate_roadmap_tutor_lesson(
    *, roadmap, content_type, item, level=None
):
    system_prompt = """
You are an expert instructor and career tutor who teaches complete,
end-to-end lessons. You write self-contained teaching content: a learner
who follows your lesson from top to bottom should understand the topic,
practice it hands-on, and be able to prove they mastered it — without
needing any external links, courses, or books. Keep every part relevant
to the target role and honest about what the learner has not done yet.
""".strip()

    level_line = (
        f"\nTARGET DIFFICULTY LEVEL:\n{level}\n"
        "Match depth and pace to this level: a beginner lesson builds "
        "from first principles with simpler language, while an advanced "
        "lesson assumes the fundamentals and goes deeper into design "
        "trade-offs, scale, and production concerns.\n"
        if level
        else ""
    )

    user_prompt = f"""
Write one complete, detailed lesson that teaches the selected roadmap
item from fundamentals to mastery. Use the full roadmap only as context;
do not change the selected goal. The lesson must be self-contained: put
the actual teaching content in your answer, never references to
elsewhere.
{level_line}

TARGET ROLE:
{roadmap.get("target_role", "")}

ROADMAP SUMMARY:
{roadmap.get("summary", "")}

SELECTED ITEM TYPE:
{content_type}

SELECTED ITEM:
{item}

Return all of the following:
- title: a specific lesson title
- overview: two or three sentences on what this lesson covers and why it
  matters for the target role
- learning_objectives: 4 to 6 concrete outcomes the learner can do after
  finishing
- prerequisites: 2 to 4 things the learner should already know (empty
  list only if none)
- key_concepts: 5 to 8 core terms or ideas, each phrased so its meaning
  is clear from the string itself
- sections: 5 to 7 teaching sections that carry the real content, in
  order: start with foundations ("what it is and why it exists"), then
  core mechanics with concrete detail, then deeper usage, then applied
  or production concerns for the target role. Each section needs a
  clear heading and 80 to 150 words of substantive explanation — no
  filler, no "learn about X" placeholders. Write the explanation itself,
  as if teaching a one-on-one student.
- walkthrough: an ordered, hands-on set of steps the learner performs
  to build or run something small that uses this item
- example: one concrete worked example (short code snippet, config, or
  annotated output) explained line by line and tied to the target role
- common_mistakes: 3 to 5 mistakes learners make with this item and how
  to avoid each
- practice_exercises: 5 to 8 exercises with enough instruction that the
  learner can start immediately, graded from easy to challenging
- project_challenge: one end-to-end mini project that combines this
  item with related roadmap skills, describing the goal, the steps, and
  what "done" looks like
- assessment_questions: 4 to 6 questions the learner answers to test
  themselves (do not include the answers)
- checkpoint: one best self-check question summarizing the core idea
- mastery_checklist: 4 to 7 observable signs the learner has mastered
  this item
- next_steps: 3 to 5 concrete actions to take right after this lesson,
  pointing at the rest of the roadmap
- estimated_time: realistic total time to finish the lesson, for
  example "90 minutes"

Do not invent candidate experience or claim that the learner has
completed anything. Never tell the learner to open an external link or
course. Use plain language and short paragraphs.
""".strip()

    return generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=RoadmapTutorLesson,
        max_retries=2,
        max_output_tokens=8192,
    )
