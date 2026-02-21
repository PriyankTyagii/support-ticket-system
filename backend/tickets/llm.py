"""
LLM Integration — Groq (llama-3.1-8b-instant)

Chosen because:
  - Groq offers a FREE tier with no credit card required (console.groq.com).
  - llama-3.1-8b-instant is one of the fastest LLMs available anywhere — typical
    response times are under 200ms, ideal for real-time ticket classification.
  - The Groq SDK is OpenAI-compatible, keeping the integration simple and portable.
  - The free tier is generous enough for development and moderate production use.
"""

import json
import logging
import os

from groq import Groq, APIError

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"billing", "technical", "account", "general"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}

# ---------------------------------------------------------------------------
# Prompt design rationale:
#  1. Each category and priority is defined with concrete domain examples so the
#     model doesn't have to guess — reduces ambiguous classifications.
#  2. The model is explicitly told to output ONLY raw JSON with no markdown or
#     explanation.  A tight max_tokens (64) enforces this.
#  3. We validate the parsed values against the allowed choice sets before using
#     them, so garbage output is caught cleanly.
# ---------------------------------------------------------------------------
CLASSIFY_PROMPT = """\
You are a support ticket triage assistant. Given a user's support ticket description, \
classify it into exactly one category and one priority level.

Categories:
- billing   : payment issues, invoices, charges, refunds, subscriptions, pricing
- technical : bugs, errors, crashes, performance problems, API/integration issues
- account   : login, password reset, profile settings, permissions, access control
- general   : anything that does not clearly fit the above three categories

Priority levels:
- critical : system completely down, data loss, active security breach, full outage
- high     : major feature broken, significant business impact, many users affected
- medium   : partial functionality impaired, moderate inconvenience, workaround exists
- low      : cosmetic issue, general question, feature request, no time pressure

Respond with ONLY a valid JSON object — no markdown, no explanation, no extra text:
{"category": "<billing|technical|account|general>", "priority": "<low|medium|high|critical>"}

Ticket description:
{description}
"""


def classify_ticket(description: str) -> dict:
    """
    Call the Groq API to classify a ticket description.
    Returns {"suggested_category": ..., "suggested_priority": ...}.
    Falls back to safe defaults on any failure so ticket submission is never blocked.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY not set — skipping LLM classification.")
        return _default_response()

    try:
        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # Free, extremely fast (~150-200ms)
            max_tokens=64,
            temperature=0,                   # Deterministic output for classification
            messages=[
                {
                    "role": "user",
                    "content": CLASSIFY_PROMPT.format(description=description.strip()),
                }
            ],
        )

        raw_text = completion.choices[0].message.content.strip()

        # Strip accidental markdown fences if the model adds them despite instructions
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        data = json.loads(raw_text)

        category = data.get("category", "").lower()
        priority = data.get("priority", "").lower()

        if category not in VALID_CATEGORIES or priority not in VALID_PRIORITIES:
            logger.warning("LLM returned out-of-range values: %s", data)
            return _default_response()

        return {"suggested_category": category, "suggested_priority": priority}

    except json.JSONDecodeError as exc:
        logger.error("LLM response was not valid JSON: %s", exc)
        return _default_response()
    except APIError as exc:
        logger.error("Groq API error: %s", exc)
        return _default_response()
    except Exception as exc:
        logger.error("Unexpected error during LLM classification: %s", exc)
        return _default_response()


def _default_response() -> dict:
    return {"suggested_category": "general", "suggested_priority": "medium"}
