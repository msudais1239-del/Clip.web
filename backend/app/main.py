from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import aiofiles
import uuid
import subprocess
import shutil
import requests
from yt_dlp import YoutubeDL
import tempfile
import numpy as np
import soundfile as sf

app = FastAPI(title="Clip.web Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.environ.get('DATA_DIR', '/data')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
CLIP_DIR = os.path.join(DATA_DIR, 'clips')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)

app.mount('/clips', StaticFiles(directory=CLIP_DIR), name='clips')

def compute_best_start(input_path: str, clip_duration: int = 20, window_sec: int = 1):
    """
    Naive automatic highlight selection based on audio RMS energy.
    - Extracts audio to a temporary WAV file
    - Computes RMS per `window_sec` and finds the highest-energy contiguous range of length `clip_duration`.
    Returns start time in seconds (float).
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name
        # extract audio as mono 16k WAV
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vn', '-ac', '1', '-ar', '16000', '-f', 'wav', wav_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        data, sr = sf.read(wav_path)
        if data.ndim > 1:
            data = np.mean(data, axis=1)
        total_samples = len(data)
        window_samples = int(window_sec * sr)
        clip_samples = int(clip_duration * sr)
        if total_samples <= clip_samples:
            return 0

        # compute RMS per window
        rms = []
        for start in range(0, total_samples, window_samples):
            end = min(start + window_samples, total_samples)
            segment = data[start:end]
            if len(segment) == 0:
                rms.append(0.0)
            else:
                rms_val = np.sqrt(np.mean(segment.astype(float)**2))
                rms.append(rms_val)
        rms = np.array(rms)

        # sliding sum over windows matching clip duration
        windows_per_clip = int(np.ceil(clip_samples / window_samples))
        if windows_per_clip <= 1:
            best_idx = int(np.argmax(rms))
            start_sec = best_idx * window_sec
            return float(start_sec)

        # compute moving sum
        cumsum = np.cumsum(np.insert(rms, 0, 0))
        sums = cumsum[windows_per_clip:] - cumsum[:-windows_per_clip]
        best_block = int(np.argmax(sums))
        start_sec = best_block * window_sec
        # clamp to valid range
        max_start = (total_samples - clip_samples) / sr
        start_sec = min(start_sec, max_start)
        if start_sec < 0:
            start_sec = 0
        return float(start_sec)
    except Exception:
        # If anything fails, fallback to start=0
        return 0
    finally:
        try:
            os.remove(wav_path)
        except Exception:
            pass

@app.post('/upload')
async def upload(file: UploadFile | None = File(None), url: str | None = Form(None)):
    # Save uploaded file or download from URL
    if file is None and not url:
        raise HTTPException(status_code=400, detail='No file or URL provided')

    if url:
        # Use yt-dlp for known platforms (YouTube/Twitch), otherwise fallback to requests
        try:
            lower = url.lower()
            if 'youtube.com' in lower or 'youtu.be' in lower or 'twitch.tv' in lower:
                # download via yt-dlp into uploads dir
                temp_template = os.path.join(UPLOAD_DIR, str(uuid.uuid4()) + '.%(ext)s')
                ydl_opts = {
                    'outtmpl': temp_template,
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                    'merge_output_format': 'mp4',
                    'quiet': True,
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    ext = info.get('ext') or 'mp4'
                # pick the newest file in uploads
                all_files = [os.path.join(UPLOAD_DIR,f) for f in os.listdir(UPLOAD_DIR)]
                input_path = max(all_files, key=os.path.getmtime)
            else:
                temp_name = str(uuid.uuid4()) + os.path.splitext(url)[-1].split('?')[0]
                out_path = os.path.join(UPLOAD_DIR, temp_name)
                r = requests.get(url, stream=True, timeout=30)
                r.raise_for_status()
                with open(out_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                input_path = out_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Failed to download URL: {e}')
    else:
        filename = file.filename or (str(uuid.uuid4()) + '.mp4')
        save_path = os.path.join(UPLOAD_DIR, filename)
        async with aiofiles.open(save_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        input_path = save_path

    # Automatic highlight selection (audio-energy based)
    start_sec = compute_best_start(input_path, clip_duration=20, window_sec=1)

    # Basic clip extraction: 20 seconds from start_sec
    clip_name = str(uuid.uuid4()) + '.mp4'
    clip_path = os.path.join(CLIP_DIR, clip_name)
    try:
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-ss', str(start_sec), '-t', '20',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', clip_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f'ffmpeg error: {e.stderr.decode() if e.stderr else e}')

    # Transcription is not included in the lightweight image. srt_url is None by default.
    srt_url = None

    clip_url = f'/clips/{clip_name}'
    return JSONResponse({'clip_url': clip_url, 'srt_url': srt_url})
