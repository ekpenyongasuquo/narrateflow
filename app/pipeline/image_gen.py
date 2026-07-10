from pathlib import Path
from genblaze_core import Pipeline, Modality
from genblaze_openai import DalleProvider
from genblaze_openai.dalle import _build_dalle_registry
from app.core.storage import get_b2_sink, get_output_dir
from app.core.config import settings


def generate_scene_image(
    job_id: str,
    section_number: int,
    prompt: str,
    attempt: int = 1,
) -> dict:
    """
    Generate a single scene image via DALL-E/GPT-Image and upload to B2.
    Returns dict with b2_url, sha256, size_bytes, run_id, manifest_uri.
    """
    output_dir = get_output_dir(job_id) / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)

    sink = get_b2_sink()

    provider = DalleProvider(
        api_key=settings.openai_api_key,
        output_dir=str(output_dir),
        models=_build_dalle_registry(),
    )

    run, manifest = (
        Pipeline(f"narrateflow-image-{job_id}-s{section_number}-a{attempt}")
        .step(
            provider,
            model="gpt-image-1",
            prompt=prompt,
            modality=Modality.IMAGE,
            size="1024x1024",
            quality="auto",
        )
        .run(
            sink=sink,
            timeout=120,
            raise_on_failure=True,
        )
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
        "attempt": attempt,
    }