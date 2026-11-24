"""Windows desktop shell around the shared local FastAPI application."""
import threading
import time
import urllib.request

import uvicorn
import webview

from app import app


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
    webview.create_window("Khensoz Universal Downloader", "http://127.0.0.1:8765", width=1100, height=800)
    webview.start()
