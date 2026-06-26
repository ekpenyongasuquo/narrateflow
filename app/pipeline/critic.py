import base64
import httpx
from app.core.config import settings

def evaluate_scene_image(
    image_path: str,
    clinical_description: str,
    section_heading: str
) -> dict:
    """
    Sends image to GPT-4o vision for clinical accuracy evaluation.
    Returns evaluation dict with retry decision.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Evaluate this medical education image.
Section: {section_heading}
Clinical description: {clinical_description}

Return JSON only:
{{
  "visual_match": 0.0-1.0,
  "safety_flag": true/false,
  "age_appropriate": true,
  "issues": ["list of issues if any"],
  "retry_reason": "string or null",
  "approved": true/false
}}
Approve if visual_match >= 0.7 and safety_flag is false."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
    )

    import json
    raw = response.choices[0].message.content
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)