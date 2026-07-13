import subprocess
from pathlib import Path
import httpx
from app.core.storage import get_presigned_url, b2_url_to_key


def _download_b2_file(b2_url: str, dest_path: Path) -> Path:
    """Download a private B2 file using a presigned URL."""
    b2_key = b2_url_to_key(b2_url)
    presigned_url = get_presigned_url(b2_key, expiry_seconds=3600)
    with httpx.Client(timeout=300) as client:
        with client.stream("GET", presigned_url) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
    return dest_path


def assemble_video(
    job_id: str,
    sections: list,
    output_dir: Path,
) -> Path:
    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []

    for item in sections:
        section_num = item["section"]["section_number"]

        print(f"[{job_id}] downloading image for section {section_num}")
        image_path = clips_dir / f"scene_{section_num}.png"
        _download_b2_file(item["image_path"], image_path)
        print(f"[{job_id}] image downloaded: {image_path.stat().st_size} bytes")

        print(f"[{job_id}] downloading audio for section {section_num}")
        audio_path = clips_dir / f"narration_{section_num}.mp3"
        _download_b2_file(item["audio_path"], audio_path)
        print(f"[{job_id}] audio downloaded: {audio_path.stat().st_size} bytes")

        clip_path = clips_dir / f"clip_{section_num}.mp4"
        print(f"[{job_id}] running ffmpeg for section {section_num}")
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(clip_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed for section {section_num}: {result.stderr[-500:]}"
            )
        print(f"[{job_id}] clip created: {clip_path}")
        clip_paths.append(str(clip_path))

    concat_file = output_dir / "concat.txt"
    concat_file.write_text(
        "\n".join([f"file '{p}'" for p in clip_paths])
    )

    final_path = output_dir / "final_video.mp4"
    print(f"[{job_id}] concatenating clips")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(final_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed: {result.stderr[-500:]}")

    print(f"[{job_id}] final video ready: {final_path}")
    return final_path