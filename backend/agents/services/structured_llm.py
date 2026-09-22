import json
import os
from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError


T = TypeVar("T", bound=BaseModel)


def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def get_model():
    return os.getenv(
        "OPENROUTER_MODEL",
        "mistralai/mistral-7b-instruct",
    )


def clean_json_response(content: str) -> str:
    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


def generate_structured_output(
    system_prompt,
    user_prompt,
    schema: Type[T],
    max_retries=1,
):
    client = get_client()
    model = get_model()

    current_prompt = user_prompt
    last_error = None

    # Generate a compact representation of the actual Pydantic schema.
    schema_json = schema.model_json_schema()

    for attempt in range(max_retries + 1):

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": current_prompt,
                    },
                ],
                temperature=0.1,
                response_format={
                    "type": "json_object"
                },
                max_tokens=800,
            )

            content = response.choices[0].message.content

            print(
                f"\n========== STRUCTURED LLM ATTEMPT "
                f"{attempt + 1} =========="
            )
            print(content)
            print("==========================================\n")

            if not content:
                raise ValueError(
                    "LLM returned an empty response."
                )

            cleaned = clean_json_response(content)

            data = json.loads(cleaned)

            result = schema.model_validate(data)

            return result

        except (
            json.JSONDecodeError,
            ValidationError,
            ValueError,
        ) as exc:

            last_error = exc

            current_prompt = (
                "Your previous response did not match the required "
                "output structure.\n\n"

                "Generate the requested information again.\n\n"

                "IMPORTANT:\n"
                "- Return the actual requested data.\n"
                "- Do NOT return a JSON schema.\n"
                "- Do NOT return field definitions.\n"
                "- Do NOT return '$defs'.\n"
                "- Do NOT return 'properties'.\n"
                "- Do NOT return 'required'.\n"
                "- Do NOT return markdown.\n"
                "- Do NOT return JSON code fences.\n"
                "- Return ONLY one valid JSON object.\n"
                "- Include every required field.\n"
                "- Use empty arrays when a list field has no information.\n"
                "- Use empty strings when a string field has no information.\n"
                "- Do NOT invent information.\n"
                "- Preserve the evidence-based rules from the original request.\n\n"

                "STRICT TYPE REQUIREMENTS:\n"
                "- Every field MUST use the exact JSON type required by the schema.\n"
                "- If the schema says list[str], every item must be a plain string.\n"
                "- If the schema says string, return a JSON string.\n"
                "- If the schema says list, return a JSON array.\n"
                "- Do NOT replace strings with objects or dictionaries.\n\n"

                "The required output schema is:\n"
                + json.dumps(schema_json, indent=2)
                + "\n\n"

                "Original request:\n"
                + user_prompt
                + "\n\n"

                "Previous validation error:\n"
                + str(exc)
                + "\n\n"

                "Fix the validation error and return ONLY the corrected "
                "JSON object."
            )
    raise ValueError(
        f"Failed to generate valid structured output after "
        f"{max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )