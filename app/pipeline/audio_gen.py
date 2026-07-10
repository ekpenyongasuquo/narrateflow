from pathlib import Path
from genblaze_core import Pipeline, Modality
from genblaze_openai import OpenAITTSProvider
from app.core.storage import get_b2_sink, get_output_dir
from app.core.config import settings


def generate_narration_audio(
    job_id: str,
    section_number: int,
    narration_text: str,
    voice: str = "nova",
) -> dict:
    """
    Generate narration audio via OpenAI TTS and upload to B2.
    Returns dict with b2_url, sha256, and manifest info.
    """
    output_dir = get_output_dir(job_id) / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    sink = get_b2_sink()

    run, manifest = (
        Pipeline(f"narrateflow-audio-{job_id}-s{section_number}")
        .step(
            OpenAITTSProvider(
                api_key=settings.openai_api_key,
                output_dir=str(output_dir),
            ),
            model="tts-1-hd",
            prompt=narration_text,
            modality=Modality.AUDIO,
            voice=voice,
            response_format="mp3",
        )
        .run(sink=sink, timeout=60, raise_on_failure=True)
    )

    step = run.steps[0]
    asset = step.assets[0]

    return {
        "b2_url": asset.url,
        "sha256": asset.sha256,
        "size_bytes": asset.size_bytes,
        "run_id": manifest.run.run_id,
        "manifest_uri": manifest.manifest_uri,
        "section_number": section_number,
    }