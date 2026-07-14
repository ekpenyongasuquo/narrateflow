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