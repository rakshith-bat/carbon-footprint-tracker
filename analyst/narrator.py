import os
import json
import anthropic
from config import Config


FALLBACK_TEMPLATE = """
Based on your data: your average daily emission is {personal_avg}kg CO2, 
compared to the {state} average of {state_baseline}kg. 
Your trend is {trend}. You are currently on a {streak}-day streak.
{goal_line}
Focus area today: {dominant_category}.
"""


def generate_narrative(report: dict, user_state: str) -> str:
    """
    Takes the analyst report dict and returns a plain-English paragraph.
    Uses Claude API if key is available, falls back to template otherwise.
    """
    api_key = Config.ANTHROPIC_API_KEY

    if not api_key:
        return _fallback_narrative(report, user_state)

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a carbon footprint analyst embedded in an environmental tracking app.
A user's daily data has been processed. Here is their structured report:

{json.dumps(report, indent=2)}

Their state/region: {user_state}

Write a 3-4 sentence analysis. Be direct, specific, and use the actual numbers.
Tell them: what's happening with their emissions, one thing causing it, 
and one specific action they can take today to improve their score or protect their streak.
Do not use bullet points. Do not be generic. Sound like a real analyst, not a chatbot.
If they have an anomaly today, acknowledge it but be calm about it.
"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()

    except Exception as e:
        print(f"Narrator API error: {e}")
        return _fallback_narrative(report, user_state)


def _fallback_narrative(report: dict, user_state: str) -> str:
    avg = report.get('personal_avg')
    if avg is None:
        return "Not enough data yet. Log a few days to unlock your analysis."

    goal_line = ""
    if report.get('on_track') is True:
        goal_line = "You're on track to meet your monthly goal."
    elif report.get('on_track') is False:
        goal_line = "At your current pace, you may exceed your monthly goal."

    return FALLBACK_TEMPLATE.format(
        personal_avg=avg,
        state=user_state,
        state_baseline=report.get('state_baseline', 8.5),
        trend=report.get('trend', 'stable'),
        streak=report.get('streak', 0),
        goal_line=goal_line,
        dominant_category=report.get('dominant_category', 'electricity')
    ).strip()