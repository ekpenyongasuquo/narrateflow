import json
from datetime import datetime, timezone
from pathlib import Path

class PipelineLogger:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.entries = []

    def log(self, event: str, data: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_id": self.job_id,
            "event": event,
            "data": data
        }
        self.entries.append(entry)
        print(f"[{self.job_id}] {event}: {data}")

    def save(self, output_dir: Path) -> Path:
        log_path = output_dir / "pipeline_log.json"
        log_path.write_text(json.dumps(self.entries, indent=2))
        return log_path