from app.pipeline.image_gen import generate_scene_image

def test_generate_scene_image():
    result = generate_scene_image(
        job_id="test-image-001",
        section_number=1,
        prompt="A Nigerian nurse in a clinical setting demonstrating proper hand washing technique at a hospital sink, bright lighting, educational illustration style, professional medical setting",
        attempt=1,
    )
    print(f"\n✅ B2 URL: {result['b2_url']}")
    print(f"✅ SHA256: {result['sha256']}")
    print(f"✅ Size: {result['size_bytes']} bytes")
    print(f"✅ Run ID: {result['run_id']}")
    print(f"✅ Manifest: {result['manifest_uri']}")

    assert result["b2_url"].startswith("https://")
    assert result["sha256"] is not None
    assert result["size_bytes"] > 0