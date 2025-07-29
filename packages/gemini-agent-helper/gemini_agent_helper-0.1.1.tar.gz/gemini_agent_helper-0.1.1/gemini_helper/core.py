# gemini_helper/core.py

import os
from dotenv import load_dotenv
from agents import AsyncOpenAI, OpenAIChatCompletionsModel , set_tracing_disabled

def get_gemini_model(model_name="gemini-2.0-flash"):
    load_dotenv()
    set_tracing_disabled(True)
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    
    provider = AsyncOpenAI(
        api_key = gemini_api_key,
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
    )

    model = OpenAIChatCompletionsModel(
        model = model_name,
        openai_client = provider
    )
    return model