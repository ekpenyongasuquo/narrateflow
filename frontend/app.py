import streamlit as st
import httpx
import time

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "https://narrateflow-rafx.onrender.com"

st.set_page_config(
    page_title="NarrateFlow",
    page_icon="🏥",
    layout="centered"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align: center; padding: 20px 0'>
    <h1>🏥 NarrateFlow</h1>
    <p style='font-size: 18px; color: #666'>
        Autonomous Medical Education Video Generator<br>
        <em>Powered by Genblaze · Stored on Backblaze B2</em>
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Wake up API on page load ──────────────────────────────────────────────────
if "api_awake" not in st.session_state:
    with st.spinner("Connecting to NarrateFlow API..."):
        try:
            httpx.get(f"{API_BASE}/ping", timeout=60)
            st.session_state["api_awake"] = True
        except Exception as e:
            st.warning(f"API may be slow to respond: {e}")
            st.session_state["api_awake"] = False

# ── Input Form ────────────────────────────────────────────────────────────────
st.subheader("📋 Generate a Training Video")

with st.form("generate_form"):
    procedure_title = st.text_input(
        "Clinical Procedure Title",
        placeholder="e.g. Hand Hygiene Before Patient Contact",
        help="Enter the name of the clinical procedure to generate a training video for"
    )

    col1, col2 = st.columns(2)
    with col1:
        audience_level = st.selectbox(
            "Target Audience",
            options=["community_health_worker", "nurse", "doctor"],
            format_func=lambda x: {
                "community_health_worker": "👷 Community Health Worker",
                "nurse": "👩‍⚕️ Nurse",
                "doctor": "🩺 Doctor"
            }[x]
        )
    with col2:
        num_sections = st.slider(
            "Number of Sections",
            min_value=2,
            max_value=5,
            value=3,
            help="More sections = longer video + higher cost"
        )

    language = st.selectbox(
        "Language",
        options=["English", "Pidgin English", "Hausa", "Yoruba", "Igbo"],
    )

    submitted = st.form_submit_button(
        "🎬 Generate Video",
        use_container_width=True,
        type="primary"
    )

# ── Job Submission ─────────────────────────────────────────────────────────────
if submitted:
    if not procedure_title.strip():
        st.error("Please enter a procedure title.")
        st.stop()

    with st.spinner("Submitting job to NarrateFlow pipeline..."):
        try:
            response = httpx.post(
                f"{API_BASE}/api/v1/generate",
                json={
                    "procedure_title": procedure_title,
                    "audience_level": audience_level,
                    "language": language,
                    "sections": num_sections,
                },
                timeout=60,
            )
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data["job_id"]
            st.session_state["job_id"] = job_id
            st.session_state["procedure_title"] = procedure_title
            st.success(f"✅ Job submitted! ID: `{job_id}`")
        except Exception as e:
            st.error(f"Failed to submit job: {e}")
            st.stop()

# ── Job Status Polling ─────────────────────────────────────────────────────────
if "job_id" in st.session_state:
    job_id = st.session_state["job_id"]
    procedure = st.session_state.get("procedure_title", "")

    st.divider()
    st.subheader(f"🔄 Pipeline Status — {procedure}")

    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    result_placeholder = st.empty()

    max_polls = 180  # 30 minutes max
    poll_interval = 10  # seconds

    for poll in range(max_polls):
        try:
            # Keep-alive ping every poll to prevent free tier spin-down
            try:
                httpx.get(f"{API_BASE}/ping", timeout=5)
            except Exception:
                pass

            status_response = httpx.get(
                f"{API_BASE}/api/v1/status/{job_id}",
                timeout=30,
            )
            status_data = status_response.json()
            status = status_data.get("status", "unknown")

            if status == "pending":
                status_placeholder.info("⏳ Job queued — pipeline starting...")
                progress_bar.progress(5)

            elif status == "running":
                elapsed = poll * poll_interval
                progress = min(10 + (elapsed // 10) * 3, 85)
                minutes = elapsed // 60
                seconds = elapsed % 60
                status_placeholder.info(
                    f"⚙️ Pipeline running... ({minutes}m {seconds}s elapsed)\n\n"
                    f"**Steps:** Script → Scene Images → Narration Audio "
                    f"→ Critic Evaluation → Video Assembly → B2 Upload"
                )
                progress_bar.progress(int(progress))

            elif status == "completed":
                progress_bar.progress(100)
                status_placeholder.success("✅ Video generation complete!")

                video_url = status_data.get("video_url")

                with result_placeholder.container():
                    st.divider()
                    st.subheader("🎬 Your Training Video")

                    if video_url:
                        st.video(video_url)
                        st.markdown(f"**[📥 Download Video]({video_url})**")
                    else:
                        st.warning("Video URL not available — check B2 bucket.")

                    st.divider()
                    st.subheader("📊 Pipeline Provenance")
                    st.markdown("""
| Component | Provider | Status |
|-----------|----------|--------|
| Script Generation | GPT-4o-mini | ✅ |
| Scene Images | gpt-image-1 via Genblaze | ✅ |
| Narration Audio | TTS-1-HD via Genblaze | ✅ |
| Critic Evaluation | GPT-4o-mini Vision | ✅ |
| Video Assembly | ffmpeg | ✅ |
| Asset Storage | Backblaze B2 | ✅ |
| Provenance Manifests | Genblaze SHA-256 | ✅ |
                    """)

                    st.info(
                        "All assets — scene images, narration audio, scripts, "
                        "Genblaze manifests, and pipeline logs — are stored on "
                        "Backblaze B2 with SHA-256 provenance tracking."
                    )

                    if st.button("🔁 Generate Another Video"):
                        del st.session_state["job_id"]
                        del st.session_state["procedure_title"]
                        st.rerun()
                break

            elif status == "failed":
                progress_bar.progress(0)
                error = status_data.get("error", "Unknown error")
                status_placeholder.error(f"❌ Pipeline failed: {error}")
                if st.button("🔁 Try Again"):
                    del st.session_state["job_id"]
                    st.rerun()
                break

            time.sleep(poll_interval)

        except Exception as e:
            status_placeholder.warning(
                f"⚠️ Polling error ({poll + 1}/{max_polls}): {e} — retrying..."
            )
            time.sleep(poll_interval)
    else:
        status_placeholder.error(
            "⏰ Timeout — pipeline is taking longer than expected. "
            "Check the Render logs or try again."
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align: center; color: #999; font-size: 13px'>
    Built for the Backblaze Generative Media Hackathon 2026<br>
    NarrateFlow · University of Calabar Teaching Hospital · Nigeria<br>
    <a href='https://github.com/ekpenyongasuquo/narrateflow'>GitHub</a> ·
    <a href='https://narrateflow-rafx.onrender.com/docs'>API Docs</a>
</div>
""", unsafe_allow_html=True)