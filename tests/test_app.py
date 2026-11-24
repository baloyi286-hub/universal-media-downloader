import unittest
from fastapi.testclient import TestClient
from app import app, checked_url, ffmpeg_location
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi import HTTPException


class SmokeTests(unittest.TestCase):
    def test_info(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/info").status_code, 200)

    def test_pwa_assets(self):
        with TestClient(app) as client:
            manifest = client.get("/static/manifest.webmanifest")
            self.assertEqual(manifest.status_code, 200)
            self.assertEqual(manifest.json()["display"], "standalone")
            self.assertIn("manifest", manifest.headers["content-type"])
            self.assertEqual(client.get("/static/sw.js").status_code, 200)
            self.assertEqual(client.get("/static/icon.svg").status_code, 200)
            self.assertEqual(client.get("/static/../app.py").status_code, 404)

    def test_home(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/").status_code, 200)

    def test_bundled_ffmpeg_detected(self):
        with TemporaryDirectory() as folder:
            ffmpeg = Path(folder) / "ffmpeg"
            ffmpeg.mkdir()
            (ffmpeg / "ffmpeg.exe").touch()
            (ffmpeg / "ffprobe.exe").touch()
            with patch("app.BASE", Path(folder)):
                self.assertEqual(ffmpeg_location(), str(ffmpeg))

    def test_private_url_rejected(self):
        for url in ("http://localhost/test", "http://127.0.0.1/test", "file:///etc/passwd"):
            with self.assertRaises(HTTPException):
                checked_url(url)


if __name__ == "__main__":
    unittest.main()
