from app.pipeline.script_gen import generate_script

def test_generate_script():
    script = generate_script(
        procedure_title="Hand Hygiene Before Patient Contact",
        audience_level="nurse",
        language="English",
        num_sections=3
    )
    print(f"\n✅ Title: {script['title']}")
    print(f"✅ Sections: {len(script['sections'])}")
    for s in script["sections"]:
        print(f"  Section {s['section_number']}: {s['heading']}")
        print(f"  Narration: {s['narration_text'][:80]}...")
        print(f"  Visual: {s['visual_prompt'][:80]}...")

    assert "title" in script
    assert "sections" in script
    assert len(script["sections"]) == 3
    for s in script["sections"]:
        assert "section_number" in s
        assert "heading" in s
        assert "narration_text" in s
        assert "visual_prompt" in s