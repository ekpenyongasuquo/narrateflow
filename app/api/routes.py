import uuid
from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import VideoJobRequest, VideoJobResponse, JobStatus
from app.pipeline.orchestrator import run_narrateflow_pipeline

router = APIRouter()
jobs = {}  # In-memory store — replace with Redis later

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
        except Exception as e:
            jobs[job_id]["status"] = JobStatus.failed
            jobs[job_id]["error"] = str(e)

    background_tasks.add_task(run_job)
    return VideoJobResponse(job_id=job_id, status=JobStatus.pending)

@router.get("/status/{job_id}", response_model=VideoJobResponse)
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return VideoJobResponse(job_id=job_id, status=JobStatus.failed, error="Job not found")
    return VideoJobResponse(
        job_id=job_id,
        status=job["status"],
        error=job.get("error")
    )