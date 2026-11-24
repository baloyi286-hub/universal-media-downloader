"""Local media downloader; use only for media you are authorized to save."""
from __future__ import annotations

import ipaddress
import os
import shutil
import socket
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DOWNLOADS = Path(os.environ.get("DOWNLOADER_DIR", str(Path.home() / "Downloads" / "UniversalDownloader"))).expanduser().resolve()
DOWNLOADS.mkdir(parents=True, exist_ok=True)
def ffmpeg_location():
    """Prefer bundled FFmpeg, then an FFmpeg installed on PATH."""
    bundled = BASE / "ffmpeg" / "ffmpeg.exe"
    probe = BASE / "ffmpeg" / "ffprobe.exe"
    if bundled.is_file() and probe.is_file():
        return str(bundled.parent)
    installed = shutil.which("ffmpeg")
    return str(Path(installed).parent) if installed else None


app = FastAPI(title="Khensoz Universal Downloader")
jobs = {}
lock = threading.RLock()
pool = ThreadPoolExecutor(max_workers=2)


class JobRequest(BaseModel):
    url: str
    kind: str = Field(default="video", pattern="^(video|audio)$")
    quality: str = Field(default="best", pattern="^(best|2160|1440|1080|720|480|360)$")
    audio_format: str = Field(default="mp3", pattern="^(mp3|m4a)$")


def checked_url(value):
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(400, "Enter a valid HTTP(S) URL")
    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise HTTPException(400, "Local addresses are not supported")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise HTTPException(400, "IP address URLs are not supported")
    return url


def public(job):
    return {key: value for key, value in job.items() if key not in ("path", "cancel")}


def update(job_id, **changes):
    with lock:
        jobs[job_id].update(changes)


def download(job_id, request):
    folder = DOWNLOADS / job_id
    folder.mkdir(parents=True, exist_ok=True)

    def hook(data):
        with lock:
            if jobs[job_id]["cancel"]:
                raise RuntimeError("Cancelled")
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            done = data.get("downloaded_bytes") or 0
            update(job_id, status="downloading", progress=round(done / total * 100, 1) if total else 0,
                   speed=data.get("_speed_str") or "", eta=data.get("_eta_str") or "")
        elif data.get("status") == "finished":
            update(job_id, status="processing", progress=99)

    try:
        options = {
            "outtmpl": str(folder / "%(title).160B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "max_filesize": 4 * 1024 ** 3,
            "socket_timeout": 25,
            "retries": 3,
            "fragment_retries": 3,
        }
        ffmpeg_dir = ffmpeg_location()
        if ffmpeg_dir:
            options["ffmpeg_location"] = ffmpeg_dir
        if request.kind == "audio":
            options["format"] = "bestaudio/best"
            options["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": request.audio_format,
                "preferredquality": "192",
            }]
        else:
            limit = "" if request.quality == "best" else "[height<=" + request.quality + "]"
            options["format"] = "bestvideo" + limit + "+bestaudio/best" + limit + "/best"
            options["merge_output_format"] = "mp4"
            options["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(request.url, download=True)
        update(job_id, title=(info or {}).get("title") or "Media")
        outputs = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() not in (".part", ".ytdl", ".temp")]
        if not outputs:
            raise RuntimeError("No output file. Check FFmpeg installation.")
        result = max(outputs, key=lambda p: p.stat().st_size)
        with lock:
            if jobs[job_id]["cancel"]:
                raise RuntimeError("Cancelled")
        update(job_id, status="completed", progress=100, filename=result.name,
               path=str(result), speed="", eta="")
    except Exception as exc:
        with lock:
            cancelled = jobs[job_id]["cancel"]
        update(job_id, status="cancelled" if cancelled else "error",
               error="Cancelled" if cancelled else str(exc)[:350])
        shutil.rmtree(folder, ignore_errors=True)


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/info")
def info():
    return {"ffmpeg": bool(ffmpeg_location()), "folder": str(DOWNLOADS)}


@app.get("/api/jobs")
def list_jobs():
    with lock:
        return [public(j) for j in reversed(list(jobs.values()))]


@app.post("/api/jobs")
def add_job(request: JobRequest):
    request.url = checked_url(request.url)
    with lock:
        if sum(j["status"] in ("queued", "downloading", "processing") for j in jobs.values()) >= 30:
            raise HTTPException(429, "Queue full")
        job_id = uuid.uuid4().hex[:12]
        jobs[job_id] = {
            "id": job_id, "url": request.url, "kind": request.kind,
            "quality": request.quality, "status": "queued", "progress": 0,
            "title": request.url, "filename": None, "error": None,
            "speed": "", "eta": "", "path": None, "cancel": False,
        }
    pool.submit(download, job_id, request)
    return {"id": job_id}


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    with lock:
        if job_id not in jobs:
            raise HTTPException(404, "Job not found")
        job = jobs[job_id]
        if job["status"] in ("completed", "cancelled", "error"):
            return {"status": job["status"]}
        job["cancel"] = True
        return {"status": "cancelling"}


@app.get("/api/jobs/{job_id}/file")
def get_file(job_id: str):
    with lock:
        job = jobs.get(job_id)
        if not job or job["status"] != "completed":
            raise HTTPException(404, "File not ready")
        path = job["path"]
    if not path or not Path(path).is_file():
        raise HTTPException(404, "File missing")
    return FileResponse(path, filename=Path(path).name, media_type="application/octet-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
