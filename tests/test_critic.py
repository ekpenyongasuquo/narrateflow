from app.pipeline.critic import evaluate_scene_image

def test_evaluate_scene_image():
    # Use a real B2 image URL from your previous test run
    # Replace this with an actual URL from your B2 bucket
    test_image_url = "https://s3.us-east-005.backblazeb2.com/narrateflow-media/narrateflow/runs/2026-07-10/a29c1372-5d52-414e-b47e-6d3d5912bbab/assets/b1a0b17d-b3d4-42b3-ab90-35da2fceeebe.png"

    # Note: above is an audio URL for structure test only
    # Replace with a real image URL after running test_image_gen.py
    result = evaluate_scene_image(
        image_url=test_image_url,
        clinical_description="A nurse demonstrating proper hand washing technique",
        section_heading="Step 1: Hand Hygiene",
    )
    print(f"\n✅ Visual match: {result.get('visual_match')}")
    print(f"✅ Safety flag: {result.get('safety_flag')}")
    print(f"✅ Professionalism: {result.get('professionalism')}")
    print(f"✅ Approved: {result.get('approved')}")
    print(f"✅ Issues: {result.get('issues')}")

    assert "approved" in result
    assert "visual_match" in result
    assert "safety_flag" in result