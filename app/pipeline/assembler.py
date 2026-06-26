import ffmpeg
from pathlib import Path

def assemble_video(job_id: str, sections: list, output_dir: Path) -> Path:
    """
    Combines per-section image + audio into a final MP4.
    Each image is held for the duration of its narration audio.
    """
    clip_paths = []

    for i, item in enumerate(sections):
        clip_path = output_dir / f"clip_{i+1}.mp4"

        (
            ffmpeg
            .input(item["image_path"], loop=1, framerate=1)
            .output(
                ffmpeg.input(item["audio_path"]),
                str(clip_path),
                vcodec="libx264",
                acodec="aac",
                shortest=None,
                pix_fmt="yuv420p",
                t=30  # max 30s per section
            )
            .overwrite_output()
            .run(quiet=True)
        )
        clip_paths.append(str(clip_path))

    # Write concat list
    concat_file = output_dir / "concat.txt"
    concat_file.write_text(
        "\n".join([f"file '{p}'" for p in clip_paths])
    )

    final_path = output_dir / "final_video.mp4"
    (
        ffmpeg
        .input(str(concat_file), format="concat", safe=0)
        .output(str(final_path), c="copy")
        .overwrite_output()
        .run(quiet=True)
    )

    return final_path