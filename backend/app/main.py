from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import aiofiles
import uuid
import subprocess
import shutil
import requests

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

@app.post('/upload')
async def upload(file: UploadFile | None = File(None), url: str | None = Form(None)):
    # Save uploaded file or download from URL
    if file is None and not url:
        raise HTTPException(status_code=400, detail='No file or URL provided')

    if url:
        # naive download — only works for public URLs
        temp_name = str(uuid.uuid4()) + os.path.splitext(url)[-1].split('?')[0]
        out_path = os.path.join(UPLOAD_DIR, temp_name)
        try:
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

    # Basic clip extraction: first 20 seconds
    clip_name = str(uuid.uuid4()) + '.mp4'
    clip_path = os.path.join(CLIP_DIR, clip_name)
    try:
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-ss', '0', '-t', '20',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', clip_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f'ffmpeg error: {e.stderr.decode() if e.stderr else e}')

    # Optional: run whisper to produce SRT if available
    srt_url = None
    try:
        import whisper
        model = whisper.load_model('small')
        result = model.transcribe(input_path)
        # write simple srt (not timestamp-accurate — placeholder)
        srt_name = clip_name.replace('.mp4', '.srt')
        srt_path = os.path.join(CLIP_DIR, srt_name)
        with open(srt_path, 'w', encoding='utf-8') as f:
            # very basic: write full transcript as one caption
            f.write('1\n00:00:00,000 --> 00:00:20,000\n')
            f.write(result.get('text',''))
        srt_url = f'/clips/{srt_name}'
    except Exception:
        # whisper not installed or failed — skip
        srt_url = None

    clip_url = f'/clips/{clip_name}'
    return JSONResponse({'clip_url': clip_url, 'srt_url': srt_url})
