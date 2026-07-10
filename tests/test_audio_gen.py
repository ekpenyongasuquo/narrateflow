from app.pipeline.audio_gen import generate_narration_audio

def test_generate_narration_audio():
    result = generate_narration_audio(
        job_id="test-audio-001",
        section_number=1,
        narration_text="Before touching any patient, it is essential to wash your hands thoroughly with soap and water for at least 20 seconds. This simple step prevents the spread of infections in the hospital.",
        voice="nova",
    )
    print(f"\n✅ B2 URL: {result['b2_url']}")
    print(f"✅ SHA256: {result['sha256']}")
    print(f"✅ Size: {result['size_bytes']} bytes")
    print(f"✅ Run ID: {result['run_id']}")
    print(f"✅ Manifest: {result['manifest_uri']}")

    assert result["b2_url"].startswith("https://")
    assert result["sha256"] is not None
    assert result["size_bytes"] > 0