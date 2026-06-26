import os
import uuid
import json
import asyncio
from pathlib import Path
from genblaze_core import Pipeline, Modality
from genblaze_openai import DalleProvider, OpenAITTSProvider
from app.core.storage import get_b2_sink
from app.core.config import settings
from app.pipeline.script_gen import generate_script
from app.pipeline.critic import evaluate_scene_image
from app.pipeline.assembler import assemble_video
from app.utils.logger import PipelineLogger

MAX_RETRIES = 3

async def run_narrateflow_pipeline(
    job_id: str,
    procedure_title: str,
    audience_level: str,
    language: str,
    num_sections: int
) -> dict:

    logger = PipelineLogger(job_id)
    output_dir = Path(settings.job_output_dir) / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    sink = get_b2_sink()
    results = {"job_id": job_id, "sections": []}

    # ── STEP 1: Script Generation ──────────────────────────
    logger.log("step_1_start", {"procedure": procedure_title})
    script = generate_script(
        procedure_title, audience_level, language, num_sections
    )
    script_path = output_dir / "script.json"
    script_path.write_text(json.dumps(script, indent=2))
    logger.log("step_1_complete", {"sections": len(script["sections"])})

    # ── STEPS 2-4: Per Section (Image → Critic → Audio) ───
    approved_sections = []

    for section in script["sections"]:
        n = section["section_number"]
        logger.log(f"section_{n}_start", section)

        # Step 2: Image Generation with retry loop
        image_path = None
        eval_result = {}
        
        for attempt in range(1, MAX_RETRIES + 1):
            img_prompt = section["visual_prompt"]
            if attempt > 1:
                img_prompt += f" (refined attempt {attempt})"

            run, manifest = (
                Pipeline(f"narrateflow-image-{job_id}-s{n}-a{attempt}")
                .step(
                    DalleProvider(
                        output_dir=str(output_dir / "frames")
                    ),
                    model="dall-e-3",
                    prompt=img_prompt,
                    modality=Modality.IMAGE,
                    size="1024x1024",
                )
                .run(sink=sink, timeout=120)
            )

            image_path = run.outputs[0].local_path

            # Step 4: Critic evaluation
            eval_result = evaluate_scene_image(
                image_path,
                section["narration_text"],
                section["heading"]
            )
            logger.log(f"section_{n}_critic_attempt_{attempt}", eval_result)

            if eval_result.get("approved"):
                logger.log(f"section_{n}_image_approved", {"attempt": attempt})
                break
            else:
                logger.log(f"section_{n}_image_rejected", eval_result)
                if attempt == MAX_RETRIES:
                    logger.log(f"section_{n}_max_retries_reached", {})

        # Step 3: Audio Generation
        audio_run, audio_manifest = (
            Pipeline(f"narrateflow-audio-{job_id}-s{n}")
            .step(
                OpenAITTSProvider(
                    output_dir=str(output_dir / "audio")
                ),
                model="tts-1-hd",
                prompt=section["narration_text"],
                modality=Modality.AUDIO,
                voice="nova",
                response_format="mp3",
            )
            .run(sink=sink, timeout=60)
        )

        audio_path = audio_run.outputs[0].local_path
        logger.log(f"section_{n}_audio_complete", {"path": audio_path})

        approved_sections.append({
            "section": section,
            "image_path": image_path,
            "audio_path": audio_path,
            "eval": eval_result,
        })

    # ── STEP 5: Video Assembly ─────────────────────────────
    logger.log("assembly_start", {"sections": len(approved_sections)})
    final_video_path = assemble_video(
        job_id, approved_sections, output_dir
    )
    logger.log("assembly_complete", {"video": str(final_video_path)})

    # ── STEP 6: Save pipeline log ──────────────────────────
    log_path = logger.save(output_dir)

    results["video_path"] = str(final_video_path)
    results["script"] = script
    results["status"] = "completed"

    return results