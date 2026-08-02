# Clip.web — AI-powered Stream Clipper (MVP)

This repository contains a runnable prototype (MVP) that accepts VOD uploads or links and generates a short highlight clip (20s) and basic crops. It uses a Next.js frontend and a FastAPI backend. Video processing uses ffmpeg; optional transcription with Whisper is supported if installed.

Important: This prototype stores files locally for development. Do NOT add API keys or secrets to the repository. See environment variables below.

Prerequisites
- Docker & docker-compose
- ffmpeg installed on the host (if you want processing locally without installing ffmpeg inside the container, ensure it is available)

Environment variables
- NEXT_PUBLIC_BACKEND_URL (default: http://localhost:8000) — frontend will use this to call backend
- OPENAI_API_KEY (optional) — if you want to use OpenAI Whisper/Cloud STT integrations (not required for the default flow)
- AWS_S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (optional) — only if you configure S3 storage

Quick start (Docker)
1. Build and run:
   docker-compose up --build

2. Open the frontend:
   http://localhost:3000

What this prototype does
- Accepts a file upload or a VOD URL (URL handling is a simple placeholder that downloads publicly accessible URLs).
- Extracts a 20s clip (starting at 0s by default) using ffmpeg and returns a downloadable link.
- Optionally will run Whisper transcription if the `whisper` package is installed and available.

Next steps
- Replace the naive clip selection with automatic highlight detection (audio energy, transcription keywords, model-based scoring).
- Add S3 storage and background workers for scalable processing.
- Add social sharing integrations (TikTok, YouTube) and moderation checks.

License: MIT
