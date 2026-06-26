import json
import uuid
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a medical education content writer for African teaching hospitals.
Generate structured instructional scripts for clinical procedures.
Always output valid JSON only — no preamble, no markdown."""

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
  "sections": [
    {{
      "section_number": 1,
      "heading": "string",
      "narration_text": "string (2-3 sentences, clear and simple)",
      "visual_prompt": "string (detailed DALL-E image prompt, clinical setting, African healthcare context)"
    }}
  ]
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    raw = response.choices[0].message.content
    return json.loads(raw)