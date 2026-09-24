import os

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()


def get_llm_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    genai.configure(api_key=api_key)
    return genai


def get_llm_model():
    return os.getenv(
        "GEMINI_MODEL",
        "gemini-1.5-flash",
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

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    generation_config = {
        "temperature": 0.2,
    }

    llm = client.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
    )

    response = llm.generate_content(full_prompt)

    # Handle both response formats
    if hasattr(response, 'text'):
        return response.text
    elif hasattr(response, 'content'):
        return response.content
    else:
        return str(response)
