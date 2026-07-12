import json
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a medical education content writer for African teaching hospitals.
Generate structured instructional scripts for clinical procedures.
Target audience ranges from community health workers to doctors.
Always output valid JSON only — no preamble, no markdown, no code blocks."""

def generate_script(
    procedure_title: str,
    audience_level: str,
    language: str,
    num_sections: int
) -> dict:
    prompt = f"""
Create a {num_sections}-section instructional script for:
Procedure: {procedure_title}
Audience: {audience_level}
Language: {language}

Return JSON with this exact structure:
{{
  "title": "string",
  "audience": "string",
  "language": "string",
  "sections": [
    {{
      "section_number": 1,
      "heading": "string",
      "narration_text": "string (2-3 clear sentences appropriate for {audience_level})",
      "visual_prompt": "string (safe educational illustration prompt: show medical equipment, diagrams, or healthcare workers in training context only — no graphic medical procedures, no bodily fluids, no distressing imagery — bright clean clinical setting, African healthcare context, professional medical education style)"
    }}
  ]
}}

Generate exactly {num_sections} sections covering the complete procedure step by step.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    return json.loads(raw)