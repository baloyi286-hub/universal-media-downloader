import unittest
from fastapi.testclient import TestClient
from app import app, checked_url
from fastapi import HTTPException


class SmokeTests(unittest.TestCase):
    def test_info(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/info").status_code, 200)

    def test_home(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/").status_code, 200)

    def test_private_url_rejected(self):
        for url in ("http://localhost/test", "http://127.0.0.1/test", "file:///etc/passwd"):
            with self.assertRaises(HTTPException):
                checked_url(url)


if __name__ == "__main__":
    unittest.main()
