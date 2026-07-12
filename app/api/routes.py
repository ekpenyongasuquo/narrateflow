import uuid
import asyncio
import threading
import json
from pathlib import Path
from fastapi import APIRouter
from app.models.schemas import VideoJobRequest, VideoJobResponse, JobStatus
from app.pipeline.orchestrator import run_narrateflow_pipeline

router = APIRouter()

JOBS_DIR = Path("/tmp/narrateflow/jobs")
JOBS_DIR.mkdir(parents=True, exist_ok=True)


def save_job(job_id: str, data: dict):
    job_file = JOBS_DIR / f"{job_id}.json"
    job_file.write_text(json.dumps(data))


def load_job(job_id: str) -> dict | None:
    job_file = JOBS_DIR / f"{job_id}.json"
    if not job_file.exists():
        return None
    return json.loads(job_file.read_text())


@router.post("/generate", response_model=VideoJobResponse)
async def generate_video(request: VideoJobRequest):
    job_id = str(uuid.uuid4())
    save_job(job_id, {"status": JobStatus.pending})

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            save_job(job_id, {"status": JobStatus.running})
            result = loop.run_until_complete(
                run_narrateflow_pipeline(
                    job_id=job_id,
                    procedure_title=request.procedure_title,
                    audience_level=request.audience_level,
                    language=request.language,
                    num_sections=request.sections,
                )
            )
            save_job(job_id, {
                "status": JobStatus.completed,
                "video_url": result.get("video_presigned_url"),
                "result": result,
            })
        except Exception as e:
            save_job(job_id, {
                "status": JobStatus.failed,
                "error": str(e),
            })
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread, daemon=False)
    thread.start()

    return VideoJobResponse(job_id=job_id, status=JobStatus.pending)


@router.get("/status/{job_id}", response_model=VideoJobResponse)
def get_job_status(job_id: str):
    job = load_job(job_id)
    if not job:
        return VideoJobResponse(
            job_id=job_id,
            status=JobStatus.failed,
            error="Job not found"
        )
    return VideoJobResponse(
        job_id=job_id,
        status=job["status"],
        video_url=job.get("video_url"),
        error=job.get("error"),
    )


@router.get("/ping")
def ping():
    return {"pong": True}


@router.get("/check-ffmpeg")
def check_ffmpeg():
    import subprocess
    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        version = result.stdout.split("\n")[0]
        return {"ffmpeg": "available", "version": version}
    return {"ffmpeg": "not_available", "error": result.stderr[:200]}