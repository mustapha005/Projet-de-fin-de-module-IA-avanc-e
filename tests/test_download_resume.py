"""Check that interrupted transfers cannot silently corrupt a dataset archive."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.download_data import transfer


class Response(io.BytesIO):
    def __init__(self, body, status, headers):
        super().__init__(body)
        self.status = status
        self.headers = headers


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "data.zip.part"
        self.path.write_bytes(b"PKbegin")
        self.url = "https://example.test/data.zip"
        self.state = self.path.with_suffix(".part.json")
        self.state.write_text(json.dumps({"url": self.url, "etag": '"version-one"', "total_bytes": 10}))

    def tearDown(self):
        self.folder.cleanup()

    def test_partial_response_appends_at_correct_offset(self):
        response = Response(b"end", 206, {"Content-Range": "bytes 7-9/10", "ETag": '"version-one"'})
        with patch("urllib.request.urlopen", return_value=response) as opened:
            self.assertEqual(transfer(self.url, self.path, "test"), 10)
        self.assertEqual(self.path.read_bytes(), b"PKbeginend")
        self.assertEqual(opened.call_args.args[0].get_header("Range"), "bytes=7-")

    def test_server_ignoring_range_restarts_instead_of_appending(self):
        response = Response(b"PKcomplete", 200, {"Content-Length": "10"})
        with patch("urllib.request.urlopen", return_value=response):
            transfer(self.url, self.path, "test")
        self.assertEqual(self.path.read_bytes(), b"PKcomplete")

    def test_incorrect_range_preserves_existing_partial(self):
        response = Response(b"end", 206, {"Content-Range": "bytes 6-8/10"})
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(ValueError, "Content-Range"):
                transfer(self.url, self.path, "test")
        self.assertEqual(self.path.read_bytes(), b"PKbegin")

    def test_challenge_page_cannot_overwrite_partial(self):
        response = Response(b"<html>challenge</html>", 200, {})
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(ValueError, "not a ZIP"):
                transfer(self.url, self.path, "test")
        self.assertEqual(self.path.read_bytes(), b"PKbegin")

    def test_changed_etag_is_rejected(self):
        response = Response(b"end", 206, {"Content-Range": "bytes 7-9/10", "ETag": '"version-two"'})
        with patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(ValueError, "ETag changed"):
                transfer(self.url, self.path, "test")
        self.assertEqual(self.path.read_bytes(), b"PKbegin")

    def test_completed_partial_can_be_recovered_without_network(self):
        with ZipFile(self.path, "w") as archive:
            archive.writestr("image.txt", "completed transfer")
        size = self.path.stat().st_size
        self.state.write_text(json.dumps({"url": self.url, "total_bytes": size}))
        with patch("urllib.request.urlopen") as opened:
            self.assertEqual(transfer(self.url, self.path, "test"), size)
            opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
