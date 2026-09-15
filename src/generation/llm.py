import os

from dotenv import load_dotenv
from google import genai


DEFAULT_MODEL = "gemini-3.6-flash"


def create_llm(
    model_name: str = DEFAULT_MODEL,
):
    """
    Create and return a Gemini client.

    The API key is loaded from the project's .env file.
    """

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Make sure it exists in the project's .env file."
        )

    return genai.Client(
        api_key=api_key
    )