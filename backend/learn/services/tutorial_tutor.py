from agents.services.structured_llm import (
    generate_structured_output,
)

from learn.schemas import TutorChatResponse


TUTOR_SYSTEM_PROMPT = """
You are an expert technical instructor teaching one learner in a chat,
in the style of the best pages on W3Schools and GeeksforGeeks.

Your job is to actually teach: give the real explanation, the working
code, and the reasoning in this reply. Never say "we will cover",
"read about X", or point to external sites, links, courses, or books —
put the teaching content directly in your answer.

Formatting rules (use the block types):
- heading: a short heading block for each new subtopic (3 to 6 words).
- paragraph: 2 to 4 sentences. Short, plain sentences. One idea each.
- code: runnable, correct code examples in the right language. Keep
  examples small and complete enough to run. Never put prose in a
  code block.
- numbered_list: steps to follow in order.
- bullet_list: key points, options, or a quick summary.
- Put the explanation of each example in paragraph blocks AFTER the
  code block, naming the output or behavior the learner should see.

Teaching rules:
- Teach exactly what the learner asked. If they ask a follow-up
  question, answer it directly and only give the background needed.
- If the request is broad ("teach me web development"), reply with a
  numbered_list roadmap of what to learn in order, then start teaching
  the first item. Ask a clarifying question only if the request is
  genuinely ambiguous.
- Match depth to the learner's level: beginner assumes nothing and
  defines terms on first use; intermediate moves faster and skips
  basics; advanced goes into internals, trade-offs, and edge cases.
- Be accurate. If you are unsure about a specific API or version
  detail, say so plainly in a paragraph instead of inventing it.
- Never invent URLs or file paths that do not exist.

Conversation rules:
- Use the conversation so far: keep terminology you already defined,
  do not restart a topic you already taught, and correct the learner
  gently if they are wrong.
- End every reply with one practice_question: a single concrete task
  or question the learner can do now to test themselves.
- Suggest exactly 3 short suggested_questions: natural next things
  the learner would ask in this same conversation.
- Return only valid JSON.
"""


def _serialize_history(history, max_messages=12):
    if not isinstance(history, list):
        return "No previous conversation."

    lines = []
    for message in history[-max_messages:]:
        if not isinstance(message, dict):
            continue

        role = message.get("role", "")
        content = message.get("content", "")

        if role == "user":
            text = str(content).strip()
            if text:
                lines.append(f"Learner: {text}")
            continue

        if role == "assistant" and isinstance(content, dict):
            lines.append(
                "Tutor: "
                + _serialize_blocks(
                    content.get("blocks", [])
                )
            )

    return "\n".join(lines) if lines else "No previous conversation."


def _serialize_blocks(blocks):
    parts = []
    if not isinstance(blocks, list):
        return ""

    for block in blocks:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type", "")

        if block_type == "heading":
            parts.append(f"## {block.get('text', '')}")
        elif block_type == "paragraph":
            parts.append(str(block.get("text", "")))
        elif block_type == "code":
            language = block.get("language", "")
            parts.append(
                f"```{language}\n{block.get('code', '')}\n```"
            )
        elif block_type in ("bullet_list", "numbered_list"):
            items = block.get("items", [])
            if isinstance(items, list):
                parts.extend(str(item) for item in items)

    return "\n".join(parts).strip()


def generate_tutor_reply(
    *,
    message,
    history=None,
    level="beginner",
):
    if not message or not str(message).strip():
        raise ValueError("Message is required.")

    prompt = f"""
The learner has sent the message below. Teach them in this reply.

LEARNER LEVEL:
{level}

CONVERSATION SO FAR:
{_serialize_history(history)}

NEW MESSAGE FROM THE LEARNER:
{str(message).strip()}

Return ONLY:
{{
  "blocks": [
    {{"type": "heading", "text": "..."}},
    {{"type": "paragraph", "text": "..."}},
    {{"type": "code", "language": "python", "code": "..."}},
    {{"type": "numbered_list", "items": ["...", "..."]}},
    {{"type": "bullet_list", "items": ["...", "..."]}}
  ],
  "practice_question": "...",
  "suggested_questions": ["...", "...", "..."]
}}
"""

    result = generate_structured_output(
        system_prompt=TUTOR_SYSTEM_PROMPT,
        user_prompt=prompt,
        schema=TutorChatResponse,
        max_retries=2,
        max_output_tokens=4096,
    )

    blocks = result.get("blocks", [])
    if not isinstance(blocks, list):
        blocks = []

    return {
        "blocks": blocks,
        "practice_question": str(
            result.get("practice_question", "")
        ),
        "suggested_questions": [
            str(question)
            for question in (
                result.get("suggested_questions", [])
                or []
            )
            if str(question).strip()
        ],
    }
