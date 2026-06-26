from pydantic import BaseModel
from enum import Enum

class AudienceLevel(str, Enum):
    community_health_worker = "community_health_worker"
    nurse = "nurse"
    doctor = "doctor"

class VideoJobRequest(BaseModel):
    procedure_title: str
    audience_level: AudienceLevel
    language: str = "English"
    sections: int = 4  # number of scenes

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class VideoJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    video_url: str | None = None
    manifest_url: str | None = None
    error: str | None = None