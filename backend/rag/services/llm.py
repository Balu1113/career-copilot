import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()


def get_llm_client():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def get_llm_model():
    return os.getenv(
        "OPENROUTER_MODEL",
        "openai/gpt-4o-mini",
    )

def generate_resume_answer(question, context):
    client = get_llm_client()

    model = get_llm_model()

    system_prompt = """
You are an AI Career Copilot.

Answer the user's question using only the
resume context provided to you.

Rules:
1. Do not invent information.
2. If the answer is not present in the context,
   clearly say that it is not available in the resume.
3. Keep the answer concise and useful.
4. Do not claim experience that the resume does not mention.
"""

    user_prompt = f"""
Resume context:

{context}

User question:

{question}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content