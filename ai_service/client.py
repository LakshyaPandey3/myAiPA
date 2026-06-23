# ai_service/client.py
# This file is the single point of contact between
# myAiPA and the Groq AI API. Every other app that
# needs AI-generated text calls get_ai_response() —
# never the Groq library directly. This means if
# myAiPA ever switches AI providers, only this one
# file needs to change — nothing else in the project.

from decouple import config
from groq import Groq

# Create the Groq client once when this module
# is first imported, using the key stored in .env.
# Never hardcode the key directly in this file.
client = Groq(api_key=config('GROQ_API_KEY'))

# The specific model myAiPA uses for all
# AI-generated text. Llama 3.3 70B is powerful,
# fast, and free on Groq's free tier.
MODEL_NAME = 'llama-3.3-70b-versatile'


def get_ai_response(prompt: str) -> str:
    """
    Send a prompt to Groq and return the text response.
    This is the ONLY function any other myAiPA app should
    call to get AI-generated text — never call the Groq
    library directly from briefing, scheduler, or any
    other app.

    If the API call fails for any reason — network issue,
    invalid key, rate limit, content safety block — we
    catch it and return a safe fallback message instead
    of crashing the request. A broken AI call should
    never take down the rest of myAiPA.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as error:
        # In production this logs to Sentry so we know
        # when Zoya is failing for real users.
        # For now we print so we can debug locally.
        print(f'AI SERVICE ERROR: {error}')
        return (
            "Zoya is having a little trouble thinking "
            "right now. Please try again in a moment."
        )