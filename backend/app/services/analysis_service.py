import logging
from openai import AsyncOpenAI
from app.config.settings import settings
from app.services.assistant_prompt import ANALYSIS_SCHEMA, ANALYSIS_INSTRUCTIONS

logger = logging.getLogger("analysis")


async def extract_structured_data(transcript: str) -> dict:
    """Runs at the end of each call (livekit_agent.py's shutdown callback) to pull
    the same structured Q1-Q5 fields Vapi's StructuredOutput resource used to
    produce, now via a direct OpenAI call against the transcript text."""
    if not transcript.strip():
        return {}
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": ANALYSIS_INSTRUCTIONS},
                {"role": "user", "content": f"Call transcript:\n\n{transcript}"},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "call_analysis",
                    "schema": ANALYSIS_SCHEMA,
                    "strict": False,
                },
            },
        )
        import json

        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        logger.exception("Structured extraction failed")
        return {}
