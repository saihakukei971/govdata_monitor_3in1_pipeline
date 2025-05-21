import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys
import requests

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.fetcher.video_fetcher import VideoFetcher


class TestVideoFetcher(unittest.TestCase):
    """VideoFetcherの動作検証: m3u8, videoタグ, aタグ展開等"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name
        self.logger = MagicMock()
        self.fetcher = VideoFetcher(data_dir=self.data_dir, logger=self.logger)

        self.source = {
            "name": "議会配信",
            "url": "https://gov.example.jp/live",
            "enabled": True
        }

    @patch("src.fetcher.video_fetcher.requests.get")
    def test_direct_video_tag(self, mock_get):
        html = '''
        <html><body>
        <video src="/stream.mp4"></video>
        </body></html>
        '''
        mock_response = MagicMock(status_code=200, text=html)
        mock_get.return_value = mock_response

        result = self.fetcher.fetch(self.source)
        self.assertIn("https://gov.example.jp/stream.mp4", result)

    @patch("src.fetcher.video_fetcher.requests.get")
    def test_source_inside_video_tag(self, mock_get):
        html = '''
        <html><body>
        <video><source src="https://gov.example.jp/s.mp4" /></video>
        </body></html>
        '''
        mock_response = MagicMock(status_code=200, text=html)
        mock_get.return_value = mock_response

        result = self.fetcher.fetch(self.source)
        self.assertIn("https://gov.example.jp/s.mp4", result)

    @patch("src.fetcher.video_fetcher.requests.get")
    def test_a_tag_to_embedded_page(self, mock_get):
        first_html = '''
        <html><body><a href="/embed/123">動画詳細</a></body></html>
        '''
        embed_html = '''
        <html><body><video src="stream_final.mp4"></video></body></html>
        '''

        def side_effect(url, *args, **kwargs):
            res = MagicMock()
            if "embed" in url:
                res.status_code = 200
                res.text = embed_html
            else:
                res.status_code = 200
                res.text = first_html
            return res

        mock_get.side_effect = side_effect

        result = self.fetcher.fetch(self.source)
        self.assertIn("stream_final.mp4", result)

    @patch("src.fetcher.video_fetcher.requests.get")
    def test_connection_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("失敗")
        result = self.fetcher.fetch(self.source)
        self.assertEqual(result, [])
        self.logger.error.assert_called()

    def tearDown(self):
        self.temp_dir.cleanup()
