# 🏥 NarrateFlow

**Autonomous Medical Education Video Generator**

Built for the [Backblaze Generative Media Hackathon 2026](https://backblaze.devpost.com)

---

## What It Does

NarrateFlow generates complete narrated clinical training videos from a single text prompt. Enter a procedure title, select your audience level, and the pipeline autonomously:

1. **Writes a structured script** — GPT-4o-mini generates section-by-section narration and visual prompts
2. **Generates scene images** — gpt-image-1 via Genblaze creates clinical illustrations for each section
3. **Narrates each section** — TTS-1-HD via Genblaze generates professional audio narration
4. **Evaluates image quality** — GPT-4o-mini Vision critic scores each image for clinical accuracy and professionalism, triggering retries if needed
5. **Assembles the final video** — ffmpeg combines images and audio into a complete MP4
6. **Stores everything on Backblaze B2** — every asset, manifest, script, and log is stored with SHA-256 provenance via Genblaze

---

## Live Demo

- **App:** https://narrateflow-rafx.onrender.com
- **API Docs:** https://narrateflow-rafx.onrender.com/docs

---

## The Problem

Doctors and nurses at teaching hospitals across Nigeria and Africa have almost no access to high-quality procedural training videos. Professional video production costs $500–$3,000 per video and weeks of production time. NarrateFlow generates a complete training video in under 5 minutes for any clinical procedure.

**Built with domain expertise from the University of Calabar Teaching Hospital (UCTH), Calabar, Nigeria.**

---

## Architecture
User Input (Procedure Title + Audience)
│
▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│         (Render.com)                    │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│         Genblaze Pipeline               │
│                                         │
│  1. Script Gen (GPT-4o-mini)            │
│  2. Image Gen (gpt-image-1)             │
│     → Critic Loop (GPT-4o-mini Vision)  │
│  3. Audio Gen (TTS-1-HD)               │
│  4. Video Assembly (ffmpeg)             │
└─────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│         Backblaze B2 Storage            │
│                                         │
│  /narrateflow/jobs/{id}/                │
│    metadata/script.json                 │
│    final/video.mp4                      │
│    logs/pipeline_log.json               │
│                                         │
│  /narrateflow/runs/{date}/{run_id}/     │
│    assets/{id}.png  (scene images)      │
│    assets/{id}.mp3  (narration audio)   │
│    manifest.json    (SHA-256 provenance)│
└─────────────────────────────────────────┘

---

## B2 Storage Architecture

Every pipeline run stores the following in Backblaze B2:

| Path | Contents |
|------|----------|
| `/narrateflow/jobs/{id}/metadata/script.json` | GPT-4o-mini generated script |
| `/narrateflow/runs/{date}/{run_id}/assets/*.png` | Scene images with SHA-256 hash |
| `/narrateflow/runs/{date}/{run_id}/assets/*.mp3` | Narration audio with SHA-256 hash |
| `/narrateflow/runs/{date}/{run_id}/manifest.json` | Genblaze provenance manifest |
| `/narrateflow/jobs/{id}/final/video.mp4` | Final assembled video |
| `/narrateflow/jobs/{id}/logs/pipeline_log.json` | Full pipeline execution log |

---

## Genblaze Integration

NarrateFlow uses the Genblaze SDK to orchestrate a multi-provider generative media pipeline:

- **`genblaze-openai`** — gpt-image-1 for scene image generation, TTS-1-HD for narration
- **`genblaze-s3`** — S3StorageBackend for Backblaze B2 integration
- **`genblaze-core`** — Pipeline orchestration, ObjectStorageSink, KeyStrategy.HIERARCHICAL, SHA-256 manifest generation

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Python 3.13 |
| Frontend | Streamlit |
| Script Generation | GPT-4o-mini |
| Image Generation | gpt-image-1 via Genblaze |
| Audio Generation | TTS-1-HD via Genblaze |
| Critic Evaluation | GPT-4o-mini Vision |
| Video Assembly | ffmpeg |
| Storage | Backblaze B2 via Genblaze S3 |
| Deployment | Render.com |

---

## Setup

```bash
git clone https://github.com/ekpenyongasuquo/narrateflow.git
cd narrateflow
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create `.env`:
```env
B2_KEY_ID=your_key_id
B2_APPLICATION_KEY=your_app_key
B2_BUCKET_NAME=narrateflow-media
B2_ENDPOINT=s3.us-east-005.backblazeb2.com
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
GMI_CLOUD_API_KEY=your_gmi_key
JOB_OUTPUT_DIR=./output
```

Run locally:
```bash
uvicorn main:app --reload
streamlit run frontend/app.py
```

---

## Built By

**Ekpenyong Mfon** — Statistician & IT Professional, University of Calabar Teaching Hospital (UCTH), Calabar, Cross River State, Nigeria.

Competing solo in the Backblaze Generative Media Hackathon 2026.
