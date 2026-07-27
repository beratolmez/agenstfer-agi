import os
from pydantic_ai.models.test import TestModel

try:
    from pydantic_ai.models.gemini import GeminiModel
except ImportError:
    GeminiModel = None

try:
    from pydantic_ai.models.openai import OpenAIModel
except ImportError:
    OpenAIModel = None


def get_llm_model():
    """Returns the Pydantic AI model instance.

    Uses Gemini API or OpenAI/Ollama model if available, else TestModel for testing.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")
    if gemini_key and GeminiModel is not None:
        return GeminiModel(model_name=gemini_model_name, api_key=gemini_key)

    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("LLM_API_KEY", "ollama")
    model_name = os.getenv("LLM_MODEL_NAME", "llama3.2")

    if OpenAIModel is not None:
        try:
            return OpenAIModel(model_name=model_name, base_url=base_url, api_key=api_key)
        except Exception:
            pass

    return TestModel()
