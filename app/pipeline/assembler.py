import subprocess
from pathlib import Path
import httpx


def _download_file(url: str, dest_path: Path) -> Path:
    """Download a file from B2 URL to local path."""
    with httpx.Client(timeout=60) as client:
        response = client.get(url)
        response.raise_for_status()
        dest_path.write_bytes(response.content)
    return dest_path


def assemble_video(
    job_id: str,
    sections: list,
    output_dir: Path,
) -> Path:
    """
    Download B2 assets per section, compose image+audio clips,
    concatenate into final MP4.
    """
    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []

    for i, item in enumerate(sections):
        section_num = item["section"]["section_number"]

        # Download image from B2
        image_path = clips_dir / f"scene_{section_num}.png"
        _download_file(item["image_path"], image_path)

        # Download audio from B2
        audio_path = clips_dir / f"narration_{section_num}.mp3"
        _download_file(item["audio_path"], audio_path)

        # Compose clip: image held for duration of audio
        clip_path = clips_dir / f"clip_{section_num}.mp4"
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
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed for section {section_num}: {result.stderr}"
            )
        clip_paths.append(str(clip_path))

    # Write concat list
    concat_file = output_dir / "concat.txt"
    concat_file.write_text(
        "\n".join([f"file '{p}'" for p in clip_paths])
    )

    # Concatenate all clips into final video
    final_path = output_dir / "final_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(final_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")

    return final_path