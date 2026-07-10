import asyncio
import pytest
from app.pipeline.orchestrator import run_narrateflow_pipeline

@pytest.mark.asyncio
async def test_full_pipeline():
    result = await run_narrateflow_pipeline(
        job_id="test-e2e-001",
        procedure_title="Hand Hygiene Before Patient Contact",
        audience_level="nurse",
        language="English",
        num_sections=2,  # 2 sections to save cost
    )

    print(f"\n✅ Status: {result['status']}")
    print(f"✅ Video B2 URL: {result['video_b2_url']}")
    print(f"✅ Video presigned URL: {result['video_presigned_url'][:80]}...")
    print(f"✅ Sections: {len(result['sections'])}")
    for s in result["sections"]:
        print(f"  Section {s['section_number']}: {s['heading']}")
        print(f"  Image: {s['image_b2_url']}")
        print(f"  Audio: {s['audio_b2_url']}")
        print(f"  Critic score: {s['critic_score']}")
        print(f"  Image manifest: {s['image_manifest']}")
        print(f"  Audio manifest: {s['audio_manifest']}")

    assert result["status"] == "completed"
    assert result["video_b2_url"].startswith("https://")
    assert len(result["sections"]) == 2
    for s in result["sections"]:
        assert s["image_b2_url"].startswith("https://")
        assert s["audio_b2_url"].startswith("https://")
        assert s["critic_score"] is not None