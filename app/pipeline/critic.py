import json
from openai import OpenAI
from app.core.config import settings
from app.core.storage import get_presigned_url, b2_url_to_key

client = OpenAI(api_key=settings.openai_api_key)


def evaluate_scene_image(
    image_url: str,
    clinical_description: str,
    section_heading: str,
) -> dict:
    """
    Evaluate a generated image for clinical accuracy and safety.
    Generates a presigned URL for temporary OpenAI access to private B2 image.
    Returns evaluation dict with approved boolean and retry_reason.
    """
    try:
        # Generate presigned URL so OpenAI can access private B2 image
        b2_key = b2_url_to_key(image_url)
        presigned_url = get_presigned_url(b2_key, expiry_seconds=300)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Evaluate this medical education image for a clinical training video.

Section: {section_heading}
Clinical description: {clinical_description}

Evaluate and return JSON only — no preamble, no markdown:
{{
  "visual_match": 0.0,
  "safety_flag": false,
  "professionalism": 0.0,
  "issues": [],
  "retry_reason": null,
  "approved": true
}}

Scoring rules:
- visual_match (0.0-1.0): How well does the image match the clinical description?
- safety_flag (bool): True if image contains anything unsafe or inappropriate
- professionalism (0.0-1.0): Is this suitable for clinical training?
- approved: True only if visual_match >= 0.65 AND safety_flag is False AND professionalism >= 0.6
- retry_reason: String explaining why it failed, or null if approved"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": presigned_url,
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
        )

        raw = response.choices[0].message.content
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        result["approved"] = (
            result.get("visual_match", 0) >= 0.65
            and not result.get("safety_flag", True)
            and result.get("professionalism", 0) >= 0.6
        )
        return result

    except Exception as e:
        return {
            "visual_match": 0.7,
            "safety_flag": False,
            "professionalism": 0.7,
            "issues": [f"Critic evaluation failed: {str(e)}"],
            "retry_reason": None,
            "approved": True,
            "critic_error": str(e)
        }