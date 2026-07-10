import json
import boto3
from pathlib import Path
from genblaze_core import Pipeline, Modality
from genblaze_openai import DalleProvider, OpenAITTSProvider
from genblaze_openai.dalle import _build_dalle_registry
from app.core.storage import get_b2_sink, get_output_dir, get_presigned_url, b2_url_to_key
from app.core.config import settings
from app.pipeline.script_gen import generate_script
from app.pipeline.critic import evaluate_scene_image
from app.pipeline.assembler import assemble_video
from app.utils.logger import PipelineLogger

MAX_RETRIES = 3


def _upload_file_to_b2(local_path: Path, b2_key: str) -> str:
    """Upload a local file to B2 and return the B2 URL."""
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.b2_endpoint}",
        aws_access_key_id=settings.b2_key_id,
        aws_secret_access_key=settings.b2_application_key,
        region_name="us-east-005",
    )
    s3.upload_file(str(local_path), settings.b2_bucket_name, b2_key)
    return f"https://{settings.b2_endpoint}/{settings.b2_bucket_name}/{b2_key}"


async def run_narrateflow_pipeline(
    job_id: str,
    procedure_title: str,
    audience_level: str,
    language: str,
    num_sections: int
) -> dict:

    logger = PipelineLogger(job_id)
    output_dir = get_output_dir(job_id)
    results = {"job_id": job_id, "sections": []}

    # ── STEP 1: Script Generation ──────────────────────────
    logger.log("step_1_start", {"procedure": procedure_title})
    script = generate_script(
        procedure_title, audience_level, language, num_sections
    )
    script_path = output_dir / "script.json"
    script_path.write_text(json.dumps(script, indent=2))

    # Upload script to B2
    script_b2_key = f"narrateflow/jobs/{job_id}/metadata/script.json"
    _upload_file_to_b2(script_path, script_b2_key)
    logger.log("step_1_complete", {
        "sections": len(script["sections"]),
        "script_b2_key": script_b2_key
    })

    # ── STEPS 2-4: Per Section (Image → Critic → Audio) ───
    approved_sections = []

    for section in script["sections"]:
        n = section["section_number"]
        logger.log(f"section_{n}_start", {"heading": section["heading"]})

        # Step 2: Image Generation with critic retry loop
        image_b2_url = None
        eval_result = {}

        for attempt in range(1, MAX_RETRIES + 1):
            img_prompt = section["visual_prompt"]
            if attempt > 1:
                img_prompt += f" Refined attempt {attempt}: {eval_result.get('retry_reason', '')}"

            frames_dir = output_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)

            image_sink = get_b2_sink()
            image_run, image_manifest = (
                Pipeline(f"narrateflow-image-{job_id}-s{n}-a{attempt}")
                .step(
                    DalleProvider(
                        api_key=settings.openai_api_key,
                        output_dir=str(frames_dir),
                        models=_build_dalle_registry(),
                    ),
                    model="gpt-image-1",
                    prompt=img_prompt,
                    modality=Modality.IMAGE,
                    size="1024x1024",
                    quality="auto",
                )
                .run(sink=image_sink, timeout=120, raise_on_failure=True)
            )

            image_step = image_run.steps[0]
            image_b2_url = image_step.assets[0].url

            # Step 4: Critic evaluation
            eval_result = evaluate_scene_image(
                image_url=image_b2_url,
                clinical_description=section["narration_text"],
                section_heading=section["heading"],
            )
            logger.log(f"section_{n}_critic_attempt_{attempt}", eval_result)

            if eval_result.get("approved"):
                logger.log(f"section_{n}_image_approved", {
                    "attempt": attempt,
                    "visual_match": eval_result.get("visual_match"),
                })
                break
            else:
                logger.log(f"section_{n}_image_rejected", eval_result)
                if attempt == MAX_RETRIES:
                    logger.log(f"section_{n}_max_retries_reached", {
                        "using_last_attempt": True
                    })

        # Step 3: Audio Generation
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        audio_sink = get_b2_sink()
        audio_run, audio_manifest = (
            Pipeline(f"narrateflow-audio-{job_id}-s{n}")
            .step(
                OpenAITTSProvider(
                    api_key=settings.openai_api_key,
                    output_dir=str(audio_dir),
                ),
                model="tts-1-hd",
                prompt=section["narration_text"],
                modality=Modality.AUDIO,
                voice="nova",
                response_format="mp3",
            )
            .run(sink=audio_sink, timeout=60, raise_on_failure=True)
        )

        audio_step = audio_run.steps[0]
        audio_b2_url = audio_step.assets[0].url
        logger.log(f"section_{n}_audio_complete", {
            "audio_b2_url": audio_b2_url
        })

        approved_sections.append({
            "section": section,
            "image_path": image_b2_url,
            "audio_path": audio_b2_url,
            "eval": eval_result,
            "image_manifest": image_manifest.manifest_uri,
            "audio_manifest": audio_manifest.manifest_uri,
        })

    # ── STEP 5: Video Assembly ─────────────────────────────
    logger.log("assembly_start", {"sections": len(approved_sections)})
    final_video_path = assemble_video(job_id, approved_sections, output_dir)
    logger.log("assembly_complete", {"video": str(final_video_path)})

    # ── STEP 6: Upload final video + logs to B2 ───────────
    video_b2_key = f"narrateflow/jobs/{job_id}/final/video.mp4"
    video_b2_url = _upload_file_to_b2(final_video_path, video_b2_key)

    log_path = logger.save(output_dir)
    log_b2_key = f"narrateflow/jobs/{job_id}/logs/pipeline_log.json"
    _upload_file_to_b2(log_path, log_b2_key)

    logger.log("pipeline_complete", {
        "video_b2_url": video_b2_url,
        "log_b2_key": log_b2_key,
    })

    results["video_b2_url"] = video_b2_url
    results["video_presigned_url"] = get_presigned_url(video_b2_key, expiry_seconds=86400)
    results["script"] = script
    results["sections"] = [
        {
            "section_number": s["section"]["section_number"],
            "heading": s["section"]["heading"],
            "image_b2_url": s["image_path"],
            "audio_b2_url": s["audio_path"],
            "image_manifest": s["image_manifest"],
            "audio_manifest": s["audio_manifest"],
            "critic_score": s["eval"].get("visual_match"),
        }
        for s in approved_sections
    ]
    results["status"] = "completed"

    return results