import uuid
from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import VideoJobRequest, VideoJobResponse, JobStatus
from app.pipeline.orchestrator import run_narrateflow_pipeline

router = APIRouter()

# In-memory job store — sufficient for hackathon demo
# Replace with Redis for production
jobs: dict = {}


@router.post("/generate", response_model=VideoJobResponse)
async def generate_video(
    request: VideoJobRequest,
    background_tasks: BackgroundTasks
):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": JobStatus.pending}

    async def run_job():
        jobs[job_id]["status"] = JobStatus.running
        try:
            result = await run_narrateflow_pipeline(
                job_id=job_id,
                procedure_title=request.procedure_title,
                audience_level=request.audience_level,
                language=request.language,
                num_sections=request.sections,
            )
            jobs[job_id]["status"] = JobStatus.completed
            jobs[job_id]["result"] = result
            jobs[job_id]["video_url"] = result.get("video_presigned_url")
        except Exception as e:
            jobs[job_id]["status"] = JobStatus.failed
            jobs[job_id]["error"] = str(e)

    background_tasks.add_task(run_job)
    return VideoJobResponse(job_id=job_id, status=JobStatus.pending)


@router.get("/status/{job_id}", response_model=VideoJobResponse)
def get_job_status(job_id: str):
    job = jobs.get(job_id)
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