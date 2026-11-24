"""Windows desktop shell around the shared local FastAPI application."""
import shutil
from pathlib import Path
import threading
import time
import urllib.request

import uvicorn
import webview

from app import app, set_download_folder, jobs, lock, DOWNLOADS


class DesktopAPI:
    def choose_folder(self):
        selected = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG, directory=str(Path.home()))
        if not selected:
            return {"cancelled": True}
        folder = selected[0] if isinstance(selected, (list, tuple)) else selected
        try:
            return {"folder": set_download_folder(folder)}
        except (OSError, ValueError) as exc:
            return {"error": str(exc)}

    def save_file(self, job_id):
        with lock:
            job = jobs.get(job_id)
            if not job or job["status"] != "completed":
                return {"error": "File not ready"}
            source = Path(job["path"])
        if not source.is_file():
            return {"error": "File no longer exists"}
        selected = webview.windows[0].create_file_dialog(
            webview.SAVE_DIALOG, directory=str(source.parent), save_filename=source.name)
        if not selected:
            return {"cancelled": True}
        target = Path(selected[0] if isinstance(selected, (tuple, list)) else selected)
        try:
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            return {"saved": str(target)}
        except OSError as exc:
            return {"error": str(exc)}


def serve():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")


if __name__ == "__main__":
    threading.Thread(target=serve, daemon=True).start()
    for _ in range(60):
        try:
            urllib.request.urlopen("http://127.0.0.1:8765/api/info", timeout=0.5).close()
            break
        except Exception:
            time.sleep(0.2)
    else:
        raise RuntimeError("Local server did not start; check whether port 8765 is in use")
    webview.create_window("Khensoz Universal Downloader", "http://127.0.0.1:8765", width=1100, height=800, js_api=DesktopAPI())
    webview.start()
