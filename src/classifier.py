import json
import os
import time
from google import genai
from google.genai import types
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a senior support triage assistant for an AI API platform.
You will receive a batch of support tickets. For each one, return a JSON array where
each element corresponds to a ticket in the order received, with exactly these keys:
- ticket_id: the ticket ID as provided
- suggested_priority: one of Critical, High, Medium, Low
- suggested_category: short category (e.g. Billing, Integration, Model Output, Performance, Safety, Onboarding)
- suggested_subcategory: short subcategory (e.g. API Timeout, Hallucination, Overage Charges)
- explanation: 1-2 sentences a support manager can act on immediately

Priority rules:
- Critical = service down, data loss, security incident
- High = major feature broken, no workaround, repeated escalation
- Medium = degraded but workable, billing confusion, intermittent issue
- Low = how-to questions, minor issues, general queries

Return ONLY the JSON array. No markdown fences, no extra text, no explanation."""


def format_ticket(ticket: dict) -> str:
    """Format a single ticket into a readable string for the prompt."""
    return f"""---
Ticket ID: {ticket.get('ticket_id', 'unknown')}
Customer: {ticket.get('customer_id', 'unknown')}
Status: {ticket.get('status', '')}
Existing category (may be blank): {ticket.get('category', '')}
Existing subcategory (may be blank): {ticket.get('subcategory', '')}
Existing priority (may be blank): {ticket.get('priority', '')}
Recurring customer: {ticket.get('is_recurrence', False)}
Prior tickets: {ticket.get('prior_ticket_ids', 'None')}
Description: {ticket.get('ticket_description', 'No description.')}
Resolution notes: {ticket.get('resolution_notes', '')}"""


def triage_batch(tickets: list[dict], retries: int = 3, backoff: int = 10) -> list[dict]:
    """
    Send a batch of tickets in one API call.
    Returns a list of triage results in the same order as input.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Check your .env file.")

    client = genai.Client(api_key=api_key)

    # Build one big prompt with all tickets in the batch
    batch_prompt = f"Triage the following {len(tickets)} support tickets. Return a JSON array with one object per ticket in order.\n\n"
    batch_prompt += "\n".join(format_ticket(t) for t in tickets)
    batch_prompt += "\n\nReturn JSON array only."

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=batch_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )

            raw = response.text.strip()

            # Strip markdown fences if model adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            parsed = json.loads(raw)

            # Make sure we got the right number of results back
            if len(parsed) != len(tickets):
                raise ValueError(f"Expected {len(tickets)} results, got {len(parsed)}")

            return parsed

        except (errors.ServerError) as e:
            if attempt < retries - 1:
                wait = backoff * (attempt + 1)
                time.sleep(wait)
            else:
                return _fallback_results(tickets, "Service unavailable after retries.")

        except (errors.ClientError) as e:
            if attempt < retries - 1:
                time.sleep(60)
            else:
                return _fallback_results(tickets, "Rate limit hit after retries.")

        except (json.JSONDecodeError, ValueError) as e:
            if attempt < retries - 1:
                time.sleep(5)
            else:
                return _fallback_results(tickets, f"Parse error: {str(e)[:100]}")

    return _fallback_results(tickets, "All retries exhausted.")


def _fallback_results(tickets: list[dict], reason: str) -> list[dict]:
    """Return graceful fallbacks for a whole batch if everything fails."""
    return [
        {
            "ticket_id": t.get("ticket_id", "unknown"),
            "suggested_priority": t.get("priority") or "Medium",
            "suggested_category": t.get("category") or "Unknown",
            "suggested_subcategory": t.get("subcategory") or "Unknown",
            "explanation": f"Auto-triage failed — {reason} Manual review needed.",
        }
        for t in tickets
    ]