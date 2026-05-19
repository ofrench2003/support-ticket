import json
import os
import time
from google import genai
from google.genai import types
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a senior support triage assistant for an AI API platform.
Given a support ticket, return ONLY valid JSON with exactly these keys:
- suggested_priority: one of Critical, High, Medium, Low
- suggested_category: short category (e.g. Billing, Integration, Model Output, Performance, Safety, Onboarding)
- suggested_subcategory: short subcategory (e.g. API Timeout, Hallucination, Overage Charges)
- explanation: 1-2 sentences a support manager can act on immediately

Priority rules:
- Critical = service down, data loss, security incident
- High = major feature broken, no workaround, repeated escalation
- Medium = degraded but workable, billing confusion, intermittent issue
- Low = how-to questions, minor issues, general queries

Return ONLY the JSON object. No markdown fences, no extra text."""


def triage_ticket(ticket: dict, retries: int = 3, backoff: int = 10) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Check your .env file.")

    client = genai.Client(api_key=api_key)

    user_msg = f"""Ticket ID: {ticket.get('ticket_id', 'unknown')}
Customer: {ticket.get('customer_id', 'unknown')}
Status: {ticket.get('status', '')}
Existing category (may be blank): {ticket.get('category', '')}
Existing subcategory (may be blank): {ticket.get('subcategory', '')}
Existing priority (may be blank): {ticket.get('priority', '')}
Recurring customer: {ticket.get('is_recurrence', False)}
Prior tickets: {ticket.get('prior_ticket_ids', 'None')}
Description: {ticket.get('ticket_description', 'No description.')}
Resolution notes: {ticket.get('resolution_notes', '')}

Triage this ticket. Return JSON only."""

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )

            raw = response.text.strip()

            # Strip markdown fences if model adds them anyway
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {
                    "suggested_priority": ticket.get("priority") or "Medium",
                    "suggested_category": ticket.get("category") or "Unknown",
                    "suggested_subcategory": ticket.get("subcategory") or "Unknown",
                    "explanation": f"Parse error on raw response: {raw[:150]}",
                }

        except errors.ServerError as e:
            # 503 — Google's servers are overloaded, wait and retry
            if attempt < retries - 1:
                wait = backoff * (attempt + 1)  # 10s, 20s, 30s
                time.sleep(wait)
            else:
                # All retries exhausted — fall back gracefully
                return {
                    "suggested_priority": ticket.get("priority") or "Medium",
                    "suggested_category": ticket.get("category") or "Unknown",
                    "suggested_subcategory": ticket.get("subcategory") or "Unknown",
                    "explanation": f"Service unavailable after {retries} attempts. Manual review needed.",
                }

        except errors.ClientError as e:
            # 429 rate limit — wait longer and retry
            if attempt < retries - 1:
                time.sleep(30)
            else:
                return {
                    "suggested_priority": ticket.get("priority") or "Medium",
                    "suggested_category": ticket.get("category") or "Unknown",
                    "suggested_subcategory": ticket.get("subcategory") or "Unknown",
                    "explanation": f"Rate limit hit after {retries} attempts. Manual review needed.",
                }